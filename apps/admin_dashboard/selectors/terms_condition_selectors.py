from django.db.models import QuerySet

from apps.admin_dashboard.models import TermsCondition


def get_terms_conditions_queryset() -> QuerySet[TermsCondition]:
    return TermsCondition.objects.all().order_by("-id")


def get_terms_condition_by_id(term_id: int) -> TermsCondition | None:
    return TermsCondition.objects.filter(id=term_id).first()
