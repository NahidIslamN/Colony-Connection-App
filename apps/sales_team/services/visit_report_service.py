"""Sales team visit report business logic."""

from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework import serializers

from apps.managements.models import (
    Colony,
    CustomerMechanary,
    CustomerNote,
    SalesRepresentative,
    VisitColony,
)

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.conf import settings
from apps.managements.services.subscription_limit_service import enforce_customer_creation_allowed
from apps.managements.services.subscription_limit_service import enforce_company_active_status_limits


@transaction.atomic
def create_customer_for_colony(sales_rep: SalesRepresentative, colony_id: int, user_payload: dict, customer_payload: dict):
    """Create a user and customer, then attach the customer to the colony atomically.

    Raises serializers.ValidationError on validation problems or returns created Customer instance.
    """
    from rest_framework import serializers

    # verify colony belongs to this sales rep
    has_permission = Colony.objects.filter(
        Q(id=colony_id, status="active") & (Q(sales_reps=sales_rep) | Q(is_public=True))
    ).exists()

    if not has_permission:
        return None

    colony = (
        Colony.objects.select_for_update()
        .prefetch_related('customers')
        .filter(id=colony_id, status="active")
        .first()
    )

    if not colony:
        return None

    company = sales_rep.company
    enforce_customer_creation_allowed(company)

    User = get_user_model()

    # create user (use a static/default password for created customers)
    email = user_payload.get('email')
    # static password: prefer setting in settings, fallback to a safe default
    default_password = getattr(settings, 'CUSTOMER_DEFAULT_PASSWORD', 'ChangeMe123!')
    full_name = user_payload.get('full_name') or customer_payload.get('owner_name')
    phone = user_payload.get('phone')
    image = user_payload.get('image')

    if User.objects.filter(email=email).exists():
        raise serializers.ValidationError({'email': 'User with this email already exists.'})

    user = User.objects.create_user(email=email, password=default_password)
    # populate user fields from owner_name/email/phone
    user.full_name = full_name or ''
    user.role = 'user'
    if phone:
        user.phone = phone
    if image and isinstance(image, InMemoryUploadedFile):
        user.image = image
    user.save()

    # create customer
    from apps.managements.models import Customer

    customer = Customer.objects.create(
        owner_company=company,
        user=user,
        owner_name=customer_payload.get('owner_name'),
        company_name=customer_payload.get('company_name'),
        industry=customer_payload.get('industry') or '',
        company_type=customer_payload.get('company_type') or '',
        email=user.email,
        phone=phone or '',
        street_address=customer_payload.get('street_address') or '',
        city=customer_payload.get('city') or '',
        state=customer_payload.get('state') or '',
        postal_code=customer_payload.get('postal_code') or '',
        country=customer_payload.get('country') or '',
        location_url=customer_payload.get('location_url') or None,
        latitude=customer_payload.get('latitude'),
        longitude=customer_payload.get('longitude'),
        is_buiesness=customer_payload.get('is_buiesness', False),
    )

    # attach to colony
    colony.customers.add(customer)

    return customer


def get_sales_rep_for_user(user):
    sales_rep = SalesRepresentative.objects.select_related("company").filter(user=user).first()
    if not sales_rep:
        return None

    enforce_company_active_status_limits(sales_rep.company)
    # sales_rep.refresh_from_db()
    # if sales_rep.status != "active":
    #     return None

    return sales_rep


def _report_related_prefetches(report_date):
    return [
        Prefetch(
            "completed_customers__customernote_set",
            queryset=CustomerNote.objects.filter(date=report_date).order_by("-created_at"),
            to_attr="report_notes",
        ),
        Prefetch(
            "completed_customers__customermechanary_set",
            queryset=CustomerMechanary.objects.filter(date=report_date).order_by("-created_at"),
            to_attr="report_mechineries",
        ),
    ]


def get_visit_colony_report_by_id_for_sales_rep(sales_rep: SalesRepresentative, visit_colony_id: int):
    report = (
        VisitColony.objects.filter(Q(id=visit_colony_id, colony__status="active") & (Q(colony__sales_reps=sales_rep) | Q(colony__is_public=True)))
        .select_related("colony")
        .prefetch_related("pending_customers", "completed_customers")
        .distinct()
        .first()
    )

    if not report:
        return None

    # if sales_rep.status != "active":
    #     raise serializers.ValidationError(
    #         {"sales_rep": "Inactive sales representative cannot perform this action."}
    #     )

    # if report.colony.status != "active":
    #     raise serializers.ValidationError(
    #         {"colony": "Inactive colony cannot be updated."}
    #     )

    return (
        VisitColony.objects.filter(id=report.id)
        .select_related("colony")
        .prefetch_related(
            "pending_customers",
            "completed_customers",
            *_report_related_prefetches(report.date),
        )
        .first()
    )


@transaction.atomic
def update_visit_colony_report_for_sales_rep(
    sales_rep: SalesRepresentative,
    visit_colony_id: int,
    validated_data: dict,
):
    has_permission = VisitColony.objects.filter(
        Q(id=visit_colony_id) & (Q(colony__sales_reps=sales_rep) | Q(colony__is_public=True))
    ).exists()

    if not has_permission:
        return None

    report = (
        VisitColony.objects.select_for_update()
        .select_related("colony")
        .prefetch_related("pending_customers", "completed_customers")
        .filter(id=visit_colony_id)
        .first()
    )
    if not report:
        return None

    completed_customer_ids = validated_data.get("completed_customer_ids")
    if completed_customer_ids is not None:
        unique_ids = list(dict.fromkeys(completed_customer_ids))
        allowed_ids = set(
            report.colony.customers.filter(id__in=unique_ids).values_list("id", flat=True)
        )
        if len(allowed_ids) != len(unique_ids):
            raise serializers.ValidationError({
                "completed_customer_ids": "One or more customers do not belong to this colony."
            })

        report.completed_customers.set(allowed_ids)
        pending_ids = report.colony.customers.exclude(id__in=allowed_ids).values_list("id", flat=True)
        report.pending_customers.set(pending_ids)

    completed_ids = set(report.completed_customers.values_list("id", flat=True))

    notes_payload = validated_data.get("notes") or []
    for note_payload in notes_payload:
        customer_id = note_payload["customer_id"]
        if customer_id not in completed_ids:
            raise serializers.ValidationError(
                {"notes": f"Customer id {customer_id} is not in completed customers."}
            )
        CustomerNote.objects.create(
            date=report.date,
            customer_id=customer_id,
            note=note_payload["note"],
        )

    mechineries_payload = validated_data.get("mechineries") or []
    for machinery_payload in mechineries_payload:
        customer_id = machinery_payload["customer_id"]
        if customer_id not in completed_ids:
            raise serializers.ValidationError(
                {"mechineries": f"Customer id {customer_id} is not in completed customers."}
            )

        CustomerMechanary.objects.update_or_create(
            date=report.date,
            customer_id=customer_id,
            serial_number=machinery_payload["serial_number"],
            defaults={
                "type": machinery_payload["type"],
                "brand": machinery_payload["brand"],
                "model": machinery_payload["model"],
                "purchase_year": machinery_payload["purchase_year"],
                "condition": machinery_payload["condition"],
                "next_nervice": machinery_payload["next_nervice"],
                "note": machinery_payload.get("note", ""),
            },
        )

    if "is_visited" in validated_data:
        report.is_visited = validated_data["is_visited"]
    elif completed_customer_ids is not None:
        report.is_visited = len(report.pending_customers.all()) == 0

    report.save(update_fields=["is_visited"])
    return (
        VisitColony.objects.filter(id=report.id)
        .select_related("colony")
        .prefetch_related(
            "pending_customers",
            "completed_customers",
            *_report_related_prefetches(report.date),
        )
        .first()
    )


@transaction.atomic
def get_visit_colony_reports_for_sales_rep(sales_rep: SalesRepresentative, report_date):
    colonies = list(
        Colony.objects.filter(Q(status="active") & (Q(sales_reps=sales_rep) | Q(is_public=True)))
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
        else:
            # Sync any newly added customers to pending_customers
            existing_completed = visit_report.completed_customers.values_list('id', flat=True)
            existing_pending = visit_report.pending_customers.values_list('id', flat=True)
            missing_customers = colony.customers.exclude(id__in=existing_completed).exclude(id__in=existing_pending)
            if missing_customers.exists():
                visit_report.pending_customers.add(*missing_customers)

    return (
        VisitColony.objects.filter(Q(date=report_date, colony__status="active") & (Q(colony__sales_reps=sales_rep) | Q(colony__is_public=True)))
        .select_related("colony")
        .prefetch_related(
            "pending_customers",
            "completed_customers",
            *_report_related_prefetches(report_date),
        )
        .distinct()
        .order_by("colony__name", "id")
    )
