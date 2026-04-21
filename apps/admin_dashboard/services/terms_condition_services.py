from dataclasses import dataclass

from django.db import IntegrityError, transaction

from apps.admin_dashboard.models import TermsCondition


@dataclass
class TermsConditionServiceError(Exception):
    code: str
    details: object | None = None

    def __str__(self):
        return self.code


@transaction.atomic
def create_terms_condition(validated_data: dict) -> TermsCondition:
    try:
        return TermsCondition.objects.create(**validated_data)
    except IntegrityError as exc:
        raise TermsConditionServiceError("integrity_error", "Unable to create terms condition due to data conflict.") from exc


@transaction.atomic
def update_terms_condition(term_id: int, validated_data: dict) -> TermsCondition:
    term = TermsCondition.objects.select_for_update().filter(id=term_id).first()
    if not term:
        raise TermsConditionServiceError("not_found", "Terms and condition not found.")

    for key, value in validated_data.items():
        setattr(term, key, value)
    term.save()
    return term


@transaction.atomic
def delete_terms_condition(term_id: int) -> None:
    term = TermsCondition.objects.select_for_update().filter(id=term_id).first()
    if not term:
        raise TermsConditionServiceError("not_found", "Terms and condition not found.")
    term.delete()
