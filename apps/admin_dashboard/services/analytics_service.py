"""System-wide analytics for admin dashboard."""

from datetime import timedelta
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone

from apps.managements.models import Company


@transaction.atomic
def get_admin_analytics():
    """Compute system-wide admin analytics snapshot.

    Returns a dict with:
    - total_companies: count with growth %
    - total_revenue: MRR sum with growth %
    - active_subscriptions: count with growth %
    - expired_plans: count with growth %
    - company_growth_trend: monthly trend (8 months)
    - revenue_trend: monthly revenue trend (8 months)
    
    Uses transaction.atomic() for read consistency and efficient annotations.
    """
    today = timezone.localdate()

    # Calculate comparison periods
    current_month_start = today.replace(day=1)
    previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    current_week_start = today - timedelta(days=today.weekday())
    previous_week_start = current_week_start - timedelta(days=7)

    # Total companies with growth
    total_companies = Company.objects.count()
    companies_prev_month = Company.objects.filter(
        user__date_joined__date__lt=current_month_start
    ).count()
    companies_growth = _calculate_growth_percent(companies_prev_month, total_companies)

    # Active subscriptions (is_subscribe=True and expire_date >= today)
    active_subs = Company.objects.filter(
        is_subscribe=True,
        expire_date__gte=today,
    ).count()
    active_subs_prev_week = Company.objects.filter(
        is_subscribe=True,
        expire_date__gte=today,
        user__date_joined__date__lt=current_week_start,
    ).count()
    active_subs_growth = _calculate_growth_percent(active_subs_prev_week, active_subs)

    # Expired plans (is_subscribe=True but expire_date < today)
    expired_plans = Company.objects.filter(
        is_subscribe=True,
        expire_date__lt=today,
    ).count()
    expired_plans_prev_week = Company.objects.filter(
        is_subscribe=True,
        expire_date__lt=today,
        user__date_joined__date__lt=current_week_start,
    ).count()
    expired_plans_growth = _calculate_growth_percent(expired_plans_prev_week, expired_plans)

    # Total revenue (MRR from subscription packages)
    revenue_data = Company.objects.filter(
        is_subscribe=True,
        subscription_package__isnull=False,
    ).aggregate(
        total_mrr=Sum('subscription_package__price_monthly')
    )
    total_revenue = revenue_data['total_mrr'] or 0

    revenue_data_prev = Company.objects.filter(
        is_subscribe=True,
        subscription_package__isnull=False,
        user__date_joined__date__lt=current_month_start,
    ).aggregate(
        total_mrr=Sum('subscription_package__price_monthly')
    )
    revenue_prev = revenue_data_prev['total_mrr'] or 0
    revenue_growth = _calculate_growth_percent(revenue_prev, total_revenue)

    # Company growth trend (monthly, last 8 months)
    company_growth_trend = _get_monthly_company_trend(months=8)

    # Revenue trend (monthly, last 8 months)
    revenue_trend = _get_monthly_revenue_trend(months=8)

    payload = {
        'total_companies': {
            'count': total_companies,
            'growth_percent': companies_growth,
            'period': 'vs last month',
        },
        'total_revenue': {
            'amount': float(total_revenue) if total_revenue else 0,
            'growth_percent': revenue_growth,
            'period': 'vs last month',
        },
        'active_subscriptions': {
            'count': active_subs,
            'growth_percent': active_subs_growth,
            'period': 'vs last week',
        },
        'expired_plans': {
            'count': expired_plans,
            'growth_percent': expired_plans_growth,
            'period': 'vs last week',
        },
        'company_growth_trend': company_growth_trend,
        'revenue_trend': revenue_trend,
    }

    return payload


def _calculate_growth_percent(previous: float, current: float) -> float:
    """Calculate growth percentage."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def _get_monthly_company_trend(months: int = 8) -> list:
    """Get monthly company creation trend for last N months."""
    from dateutil.relativedelta import relativedelta

    today = timezone.localdate()
    trend = []

    for i in range(months - 1, -1, -1):
        month_start = (today - relativedelta(months=i)).replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

        count = Company.objects.filter(
            user__date_joined__date__gte=month_start,
            user__date_joined__date__lte=month_end,
        ).count()

        trend.append({
            'month': month_start.strftime('%b'),
            'count': count,
        })

    return trend


def _get_monthly_revenue_trend(months: int = 8) -> list:
    """Get monthly revenue trend for last N months."""
    from dateutil.relativedelta import relativedelta

    today = timezone.localdate()
    trend = []

    for i in range(months - 1, -1, -1):
        month_start = (today - relativedelta(months=i)).replace(day=1)
        month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)

        revenue = Company.objects.filter(
            is_subscribe=True,
            subscription_package__isnull=False,
            user__date_joined__date__gte=month_start,
            user__date_joined__date__lte=month_end,
        ).aggregate(
            total=Sum('subscription_package__price_monthly')
        )['total'] or 0

        trend.append({
            'month': month_start.strftime('%b'),
            'revenue': float(revenue),
        })

    return trend
