import logging
import uuid

import stripe
from django.conf import settings
from django.utils import timezone

from apps.managements.models.subscribplan import SubscribePlan

logger = logging.getLogger(__name__)


class StripeCheckoutError(Exception):
    pass


def _get_stripe_api_key():
    key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not key:
        raise StripeCheckoutError("Stripe secret key not configured.")
    return key


def _validate_plan_and_duration(plan_id, duration):
    try:
        plan = SubscribePlan.objects.get(id=plan_id)
    except SubscribePlan.DoesNotExist:
        raise StripeCheckoutError("Subscription plan not found.")

    if duration not in ("monthly", "yearly"):
        raise StripeCheckoutError("Invalid plan_duration. Allowed: 'monthly' or 'yearly'.")

    # resolve amount in cents
    amount_decimal = plan.price_monthly if duration == "monthly" else plan.price_yearly
    try:
        amount_cents = int(amount_decimal * 100)
    except Exception:
        raise StripeCheckoutError("Invalid plan price configured.")

    interval = "month" if duration == "monthly" else "year"

    return plan, amount_cents, interval


def create_subscription_checkout_session(company, plan_id, plan_duration, success_url, cancel_url, request_id=None):
    """
    Create a Stripe Checkout Session for a subscription without requiring pre-created Price objects.

    - company: Company instance
    - plan_id: SubscribePlan id
    - plan_duration: 'monthly'|'yearly'
    - success_url / cancel_url: fully qualified URLs where Stripe will redirect

    Returns: dict with 'url' for checkout session and 'session_id'
    Raises: StripeCheckoutError on validation or stripe.error.* on Stripe failures
    """
    stripe.api_key = _get_stripe_api_key()

    plan, amount_cents, interval = _validate_plan_and_duration(plan_id, plan_duration)

    # Compose idempotency key using request id or a fresh uuid to avoid duplicate sessions
    idempotency_key = request_id or str(uuid.uuid4())

    # Build product name
    product_name = f"{plan.plan_Name} ({plan_duration})"

    # Prepare metadata securely: keep limited info
    metadata = {
        "company_id": str(company.id),
        "plan_id": str(plan.id),
        "plan_duration": plan_duration,
        "created_at": timezone.now().isoformat(),
    }

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            # create a dynamic price for the checkout session
            line_items=[
                {
                    "price_data": {
                        "currency": getattr(settings, "STRIPE_CURRENCY", "usd"),
                        "product_data": {"name": product_name},
                        "unit_amount": amount_cents,
                        "recurring": {"interval": interval},
                    },
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            allow_promotion_codes=True,
            # attach customer email when available for better UX without creating a Customer record
            customer_email=(company.email if getattr(company, "email", None) else None),
        )
    except Exception as exc:
        logger.error(f"Stripe checkout session creation failed: {exc}", exc_info=True)
        raise StripeCheckoutError("Failed to create Stripe checkout session.")

    return {
        "url": getattr(session, "url", None) or session.get("url"),
        "session_id": getattr(session, "id", None) or session.get("id"),
    }
