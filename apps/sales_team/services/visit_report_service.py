"""Sales team visit report business logic."""

from django.db import transaction

from apps.managements.models import Colony, SalesRepresentative, VisitColony


def get_sales_rep_for_user(user):
    return SalesRepresentative.objects.select_related("company").filter(user=user).first()


@transaction.atomic
def get_visit_colony_reports_for_sales_rep(sales_rep: SalesRepresentative, report_date):
    colonies = list(
        Colony.objects.filter(sales_reps=sales_rep)
        .select_related("colony_owner")
        .prefetch_related("customers")
        .order_by("name", "id")
    )

    if not colonies:
        return VisitColony.objects.none()

    for colony in colonies:
        visit_report, created = VisitColony.objects.select_for_update().get_or_create(
            colony=colony,
            date=report_date,
            defaults={"is_visited": False},
        )

        if created:
            visit_report.pending_customers.set(colony.customers.all())

    return (
        VisitColony.objects.filter(date=report_date, colony__sales_reps=sales_rep)
        .select_related("colony")
        .prefetch_related("pending_customers", "completed_customers")
        .distinct()
        .order_by("colony__name", "id")
    )
