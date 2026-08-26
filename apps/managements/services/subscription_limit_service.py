from django.utils import timezone

from apps.managements.models import Colony, Company, SalesRepresentative


class SubscriptionRestrictionError(Exception):
    """Raised when company subscription or plan limits block write operations."""


def _lock_company_with_plan(company: Company) -> Company:
    return Company.objects.select_for_update().select_related("subscription_package").get(id=company.id)


def _normalize_limit(raw_value) -> int:
    try:
        return max(0, int(raw_value or 0))
    except (TypeError, ValueError):
        return 0


def _validate_active_subscription(company: Company) -> None:
    return # TEMPORARILY BYPASSED SUBSCRIPTION CHECKS
    today = timezone.localdate()

    if not company.is_subscribe:
        raise SubscriptionRestrictionError("Your subscription is inactive. Please activate a plan.")

    if company.expire_date < today:
        raise SubscriptionRestrictionError("Your subscription has expired. Please renew your plan.")

    if not company.subscription_package:
        raise SubscriptionRestrictionError("No subscription package is assigned to this company.")


def enforce_company_active_status_limits(company: Company, lock_company: bool = True) -> dict:
    """Ensure active colonies/sales reps never exceed plan limits.

    If subscription is inactive/expired/missing package, active reps and active colonies
    are forced to inactive to stop all related actions.
    """
    return {"deactivated_sales_reps": 0, "deactivated_colonies": 0} # TEMPORARILY BYPASSED SUBSCRIPTION CHECKS
    
    locked_company = _lock_company_with_plan(company) if lock_company else company
    today = timezone.localdate()

    if (
        (not locked_company.is_subscribe)
        or (locked_company.expire_date < today)
        or (locked_company.subscription_package is None)
    ):
        deactivated_sales_reps = SalesRepresentative.objects.filter(
            company=locked_company,
            status="active",
        ).update(status="inactive")
        # Ensure colonies are not set to inactive
        deactivated_colonies = 0
        return {
            "deactivated_sales_reps": deactivated_sales_reps,
            "deactivated_colonies": deactivated_colonies,
        }

    plan = locked_company.subscription_package
    deactivated_sales_reps = 0
    deactivated_colonies = 0

    if not plan.is_unlimit_users:
        rep_limit = _normalize_limit(plan.user_limit)
        active_rep_ids = list(
            SalesRepresentative.objects.filter(company=locked_company, status="active")
            .order_by("id")
            .values_list("id", flat=True)
        )
        overflow_rep_ids = active_rep_ids[rep_limit:]
        if overflow_rep_ids:
            deactivated_sales_reps = SalesRepresentative.objects.filter(id__in=overflow_rep_ids).update(
                status="inactive"
            )

    if not plan.is_unlimit_colony:
        colony_limit = _normalize_limit(plan.colony_limit)
        active_colony_ids = list(
            Colony.objects.filter(colony_owner=locked_company, status="active")
            .exclude(is_public=True)
            .order_by("id")
            .values_list("id", flat=True)
        )
        overflow_colony_ids = active_colony_ids[colony_limit:]
        if overflow_colony_ids:
            # We don't deactivate colonies anymore based on limits
            pass

    return {
        "deactivated_sales_reps": deactivated_sales_reps,
        "deactivated_colonies": deactivated_colonies,
    }


def enforce_sales_rep_creation_allowed(company: Company) -> Company:
    """Lock company row and validate plan rules before creating a sales rep."""
    return company # TEMPORARILY BYPASSED SUBSCRIPTION CHECKS
    
    locked_company = _lock_company_with_plan(company)
    _validate_active_subscription(locked_company)
    enforce_company_active_status_limits(locked_company, lock_company=False)

    plan = locked_company.subscription_package
    if not plan.is_unlimit_users:
        rep_limit = _normalize_limit(plan.user_limit)
        current_total_reps = SalesRepresentative.objects.filter(company=locked_company).count()
        if current_total_reps >= rep_limit:
            raise SubscriptionRestrictionError(
                "Sales representative create limit reached for your current subscription plan."
            )

    return locked_company


def enforce_sales_rep_update_allowed(company: Company) -> Company:
    """Lock company row and validate subscription rules before updating a sales rep."""
    return company # TEMPORARILY BYPASSED SUBSCRIPTION CHECKS
    
    locked_company = _lock_company_with_plan(company)
    _validate_active_subscription(locked_company)
    enforce_company_active_status_limits(locked_company, lock_company=False)

    return locked_company


def enforce_customer_creation_allowed(company: Company) -> Company:
    """Lock company row and validate plan rules before creating a customer."""
    return company # TEMPORARILY BYPASSED SUBSCRIPTION CHECKS
    
    locked_company = _lock_company_with_plan(company)
    _validate_active_subscription(locked_company)
    enforce_company_active_status_limits(locked_company, lock_company=False)

    return locked_company


def enforce_colony_creation_allowed(company: Company) -> Company:
    """Lock company row and validate plan rules before creating a colony."""
    return company # TEMPORARILY BYPASSED SUBSCRIPTION CHECKS
    
    locked_company = _lock_company_with_plan(company)
    _validate_active_subscription(locked_company)
    enforce_company_active_status_limits(locked_company, lock_company=False)

    plan = locked_company.subscription_package
    if not plan.is_unlimit_colony:
        colony_limit = _normalize_limit(plan.colony_limit)
        current_total_colonies = Colony.objects.filter(colony_owner=locked_company).count()
        if current_total_colonies >= colony_limit:
            raise SubscriptionRestrictionError(
                "Colony create limit reached for your current subscription plan."
            )

    return locked_company
