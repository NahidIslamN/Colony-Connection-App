import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from rest_framework import status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.managements.models import (
    Company,
    Colony,
    SubscribePlan,
    Customer,
    SalesRepresentative,
    VisitColony,
)
from core.custom_permission import IsCompany
from core.pagination import CustomPagination
from core.responses import error_response, success_response


logger = logging.getLogger(__name__)


class DashboadDataAnylize(APIView):
    """Company-level analytics dashboard.

    Returns a JSON payload with summary KPIs and chart series suitable
    for the admin/company dashboard image (total colonies, customers,
    active reps, overdue/today visits, sales rep performance, weekly visits).

    ACID / consistency: read queries are wrapped in a single transaction
    block so the snapshot is consistent across the aggregated queries.
    """

    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        try:
            # find the company for the requesting user
            company = Company.objects.select_related('user').get(user=request.user)

            today = timezone.localdate()
            week_start = today - timedelta(days=6)

            # wrap reads so they are consistent together
            with transaction.atomic():
                total_colonies = Colony.objects.filter(colony_owner=company).count()
                total_customers = Customer.objects.filter(owner_company=company).count()
                active_sales_reps = SalesRepresentative.objects.filter(company=company, status='active').count()

                overdue_visits = VisitColony.objects.filter(
                    colony__colony_owner=company,
                    date__lt=today,
                    is_visited=False,
                ).count()

                todays_visits = VisitColony.objects.filter(
                    colony__colony_owner=company,
                    date=today,
                ).count()

                # Sales rep performance - top reps by number of completed customers
                reps_qs = (
                    SalesRepresentative.objects.filter(company=company)
                    .annotate(visits_completed=Count('customers__completed_colonies'))
                    .order_by('-visits_completed')
                )

                sales_rep_performance = []
                for rep in reps_qs[:6]:
                    sales_rep_performance.append(
                        {
                            'id': rep.id,
                            'full_name': getattr(rep, 'full_name', str(rep)),
                            'visits_completed': int(getattr(rep, 'visits_completed', 0) or 0),
                        }
                    )

                # Weekly visits series (last 7 days)
                visits = (
                    VisitColony.objects.filter(
                        colony__colony_owner=company,
                        date__gte=week_start,
                        date__lte=today,
                    )
                    .values('date')
                    .annotate(count=Count('id'))
                    .order_by('date')
                )

                # normalize to array of days
                daily_map = {v['date']: v['count'] for v in visits}
                weekly_visits = []
                for i in range(7):
                    d = week_start + timedelta(days=i)
                    weekly_visits.append({'date': d.isoformat(), 'count': int(daily_map.get(d, 0))})

            payload = {
                'total_colonies': total_colonies,
                'total_customers': total_customers,
                'active_sales_reps': active_sales_reps,
                'overdue_visits': overdue_visits,
                'todays_visits': todays_visits,
                'sales_rep_performance': sales_rep_performance,
                'weekly_visits': weekly_visits,
            }

            return success_response(message="data fatched",status_code=status.HTTP_200_OK,data=payload)

        except Company.DoesNotExist:
            return error_response(
                message='Company not found for this user', status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as exc:
            logger.exception('Dashboard analytics failed')
            return error_response(message=str(exc), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)