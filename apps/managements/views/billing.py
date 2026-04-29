import logging
from datetime import date, datetime, timedelta
from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.managements.models import Company
from apps.managements.models.subscribplan import Invoice, SubscribePlan, WebhookEvent
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if hasattr(value, "to_dict_recursive"):
        try:
            return _json_safe(value.to_dict_recursive())
        except Exception:
            return str(value)
    if hasattr(value, "to_dict"):
        try:
            return _json_safe(value.to_dict())
        except Exception:
            return str(value)
    return value


class BillingSuccessView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            return error_response("session_id is required.", status.HTTP_400_BAD_REQUEST)

        if not getattr(settings, "STRIPE_SECRET_KEY", None):
            return error_response("Stripe is not configured.", status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            session_obj = stripe.checkout.Session.retrieve(session_id)
            session = session_obj.to_dict_recursive() if hasattr(session_obj, "to_dict_recursive") else session_obj.to_dict()
        except stripe.error.StripeError as exc:
            logger.warning("Invalid Stripe session retrieval attempt: %s", exc)
            return error_response("Invalid checkout session.", status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error("Unexpected error retrieving Stripe session: %s", exc, exc_info=True)
            return error_response("Unable to verify checkout session.", status.HTTP_500_INTERNAL_SERVER_ERROR)

        if session.get("payment_status") != "paid":
            return error_response(
                "Checkout session has not been paid yet.",
                status.HTTP_400_BAD_REQUEST,
            )

        metadata = session.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = dict(metadata)
        company_id = metadata.get("company_id")
        plan_id = metadata.get("plan_id")
        plan_duration = metadata.get("plan_duration")

        if not company_id or not plan_id or plan_duration not in {"monthly", "yearly"}:
            return error_response(
                "Checkout session metadata is incomplete.",
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            plan = SubscribePlan.objects.get(pk=plan_id)
        except SubscribePlan.DoesNotExist:
            return error_response("Subscription plan not found.", status.HTTP_404_NOT_FOUND)

        expiration_days = 30 if plan_duration == "monthly" else 365
        expire_date = timezone.localdate() + timedelta(days=expiration_days)

        try:
            with transaction.atomic():
                company = Company.objects.select_for_update().get(pk=company_id)

                company.subscription_package = plan
                company.is_subscribe = True
                company.expire_date = expire_date
                company.save(update_fields=["subscription_package", "is_subscribe", "expire_date"])

        except Company.DoesNotExist:
            return error_response("Company not found.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error("Failed to update subscription after checkout: %s", exc, exc_info=True)
            return error_response(
                "Subscription payment was verified, but the account update failed.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success_response(
            message="Subscription activated successfully.",
            status_code=status.HTTP_200_OK,
            data={
                "session_id": session_id,
                "company_id": str(company_id),
                "plan_id": str(plan_id),
                "plan_name": plan.plan_Name,
                "plan_duration": plan_duration,
                "expire_date": expire_date.isoformat(),
                "checkout_status": session.get("status"),
            },
        )


class BillingCancelView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        return success_response(
            message="Checkout was cancelled.",
            status_code=status.HTTP_200_OK,
            data={
                "canceled": True,
                "message": "No changes were made to your subscription.",
            },
        )


class BillingWebhookView(APIView):
    """Stripe webhook endpoint. Verifies signature, is idempotent, and updates Company + Invoice.

    Handles at minimum:
      - checkout.session.completed (initial subscription)
      - invoice.payment_succeeded (renewals and initial invoice finalization)

    Security:
      - verifies `STRIPE_WEBHOOK_SECRET` via Stripe SDK
      - records processed event ids in `WebhookEvent` to ensure idempotency

    ACID:
      - updates are wrapped in `transaction.atomic()` with `select_for_update()` on Company
    """

    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

        if not webhook_secret:
            logger.error("Stripe webhook secret not configured")
            return error_response("Webhook not configured.", status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            event_obj = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=webhook_secret)
            event = event_obj.to_dict_recursive() if hasattr(event_obj, "to_dict_recursive") else event_obj.to_dict()
        except ValueError:
            # Invalid payload
            logger.exception("Invalid webhook payload")
            return error_response("Invalid payload.", status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            logger.exception("Invalid webhook signature")
            return error_response("Invalid signature.", status.HTTP_400_BAD_REQUEST)

        event = _json_safe(event)
        event_id = event.get("id")

        # Idempotency: skip already processed events
        if WebhookEvent.objects.filter(event_id=event_id).exists():
            return success_response("Event already processed.", status.HTTP_200_OK)

        event_type = event.get("type")
        data = event.get("data", {}).get("object", {}) or {}

        try:
            # Process supported event types
            if event_type == "checkout.session.completed":
                # session contains metadata and may contain `subscription` and `amount_total`
                session = data
                metadata = session.get("metadata") or {}
                if not isinstance(metadata, dict):
                    metadata = dict(metadata)

                company_id = metadata.get("company_id")
                plan_id = metadata.get("plan_id")
                plan_duration = metadata.get("plan_duration")
                subscription_id = session.get("subscription")

                if not company_id or not plan_id or plan_duration not in {"monthly", "yearly"}:
                    logger.warning("checkout.session.completed missing metadata: %s", metadata)
                    # record event for manual inspection, but return 200 so Stripe doesn't retry endlessly
                    WebhookEvent.objects.create(event_id=event_id, payload=_json_safe(event))
                    return success_response("Checkout session received but metadata incomplete.", status.HTTP_200_OK)

                expiration_days = 30 if plan_duration == "monthly" else 365
                expire_date = timezone.localdate() + timedelta(days=expiration_days)

                with transaction.atomic():
                    company = Company.objects.select_for_update().get(pk=company_id)
                    plan = SubscribePlan.objects.get(pk=plan_id)

                    company.subscription_package = plan
                    company.is_subscribe = True
                    company.expire_date = expire_date
                    if subscription_id:
                        company.stripe_subscription_id = subscription_id
                    company.save(update_fields=["subscription_package", "is_subscribe", "expire_date", "stripe_subscription_id"]) if subscription_id else company.save(update_fields=["subscription_package", "is_subscribe", "expire_date"]) 

                # create a lightweight Invoice record if possible
                try:
                    amount = session.get("amount_total")
                    currency = session.get("currency")
                    if amount is not None:
                        Invoice.objects.create(
                            company_id=company_id,
                            plan_id=plan_id,
                            payment_ammount=(Decimal(amount) / Decimal(100)),
                            stripe_invoice_id=None,
                            stripe_subscription_id=subscription_id,
                            currency=currency,
                            paid=True if session.get("payment_status") == "paid" else False,
                            metadata=_json_safe(metadata),
                        )
                except Exception:
                    logger.exception("Failed to create initial invoice from checkout.session.completed")

            elif event_type == "invoice.payment_succeeded":
                invoice = data
                invoice_id = invoice.get("id")
                subscription_id = invoice.get("subscription")
                amount_paid = invoice.get("amount_paid")
                currency = invoice.get("currency")
                metadata = invoice.get("metadata") or {}
                if not isinstance(metadata, dict):
                    metadata = dict(metadata)

                company_id = metadata.get("company_id")
                plan_id = metadata.get("plan_id")
                # try to resolve company by subscription id when metadata missing
                if not company_id and subscription_id:
                    company = Company.objects.filter(stripe_subscription_id=subscription_id).first()
                    company_id = company.id if company else None

                if not company_id:
                    logger.warning("invoice.payment_succeeded missing company mapping: %s", invoice_id)
                    WebhookEvent.objects.create(event_id=event_id, payload=_json_safe(event))
                    return success_response("Invoice received but company not found.", status.HTTP_200_OK)

                # compute expire date from invoice period_end when available
                period_end = None
                lines = invoice.get("lines", {}).get("data", [])
                if lines and isinstance(lines, list):
                    period = lines[0].get("period") or {}
                    period_end = period.get("end")

                with transaction.atomic():
                    company = Company.objects.select_for_update().get(pk=company_id)

                    # update company active subscription state and expire_date
                    company.is_subscribe = True
                    if plan_id:
                        try:
                            plan = SubscribePlan.objects.get(pk=plan_id)
                            company.subscription_package = plan
                        except SubscribePlan.DoesNotExist:
                            logger.warning("Plan id %s from invoice metadata not found", plan_id)

                    if period_end:
                        try:
                            expire_date = timezone.datetime.fromtimestamp(int(period_end)).date()
                        except Exception:
                            expire_date = timezone.localdate() + timedelta(days=30)
                    else:
                        expire_date = timezone.localdate() + timedelta(days=30)

                    company.expire_date = expire_date
                    # ensure stripe_subscription_id saved
                    if subscription_id:
                        company.stripe_subscription_id = subscription_id
                    company.save()

                    # create invoice record (idempotent by stripe_invoice_id)
                    if not Invoice.objects.filter(stripe_invoice_id=invoice_id).exists():
                        Invoice.objects.create(
                            company_id=company_id,
                            plan_id=plan_id,
                            payment_ammount=(Decimal(amount_paid) / Decimal(100)) if amount_paid is not None else Decimal("0.00"),
                            stripe_invoice_id=invoice_id,
                            stripe_subscription_id=subscription_id,
                            currency=currency,
                            paid=True,
                            metadata=_json_safe(metadata),
                        )

            else:
                # For other events, just log and store for auditing
                logger.info("Unhandled Stripe event type: %s", event_type)

            # record processed event atomically
            WebhookEvent.objects.create(event_id=event_id, payload=_json_safe(event))
            return success_response("Webhook processed.", status.HTTP_200_OK)

        except Exception as exc:
            logger.exception("Error processing webhook: %s", exc)
            # Let Stripe retry by returning 500
            return error_response("Webhook processing failed.", status.HTTP_500_INTERNAL_SERVER_ERROR)
