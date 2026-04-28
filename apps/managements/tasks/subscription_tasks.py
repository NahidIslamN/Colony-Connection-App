from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.managements.models import Company
from apps.managements.services.subscription_limit_service import enforce_company_active_status_limits


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def mark_expired_company_subscriptions(self):
    """Deactivate subscriptions whose expiry date has passed."""
    today = timezone.localdate()

    with transaction.atomic():
        updated_count = Company.objects.filter(
            is_subscribe=True,
            expire_date__lt=today,
        ).update(is_subscribe=False)

    return {
        "updated_companies": updated_count,
        "checked_date": today.isoformat(),
    }


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def enforce_company_plan_limits(self):
    """Normalize active colony/sales-rep states according to plan limits for all companies."""
    company_ids = list(Company.objects.values_list("id", flat=True))

    total_deactivated_sales_reps = 0
    total_deactivated_colonies = 0

    for company_id in company_ids:
        with transaction.atomic():
            company = Company.objects.get(id=company_id)
            result = enforce_company_active_status_limits(company)
            total_deactivated_sales_reps += result.get("deactivated_sales_reps", 0)
            total_deactivated_colonies += result.get("deactivated_colonies", 0)

    return {
        "deactivated_sales_reps": total_deactivated_sales_reps,
        "deactivated_colonies": total_deactivated_colonies,
    }
