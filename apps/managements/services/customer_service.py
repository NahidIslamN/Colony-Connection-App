from django.contrib.auth import get_user_model
from django.db import transaction

from apps.managements.models import Colony, Company, Customer, SalesRepresentative

User = get_user_model()


CUSTOMER_FIELD_MAPPING = {
    "company_owner_name": "owner_name",
    "customer_name": "company_name",
    "industry": "industry",
    "company_type": "company_type",
    "email_address": "email",
    "phone_number": "phone",
    "street_address": "street_address",
    "state_province": "state",
    "zip_postal_code": "postal_code",
    "city": "city",
    "country": "country",
}


def get_customers_for_company(company: Company):
    return (
        Customer.objects.filter(owner_company=company)
        .select_related("user")
        .prefetch_related("sales_reps", "colonies")
    )


def get_customer_by_id(customer_id: int, company: Company):
    return (
        Customer.objects.filter(id=customer_id, owner_company=company)
        .select_related("user")
        .prefetch_related("sales_reps", "colonies")
        .first()
    )


def _validate_sales_rep_ids(company: Company, sales_rep_ids: list[int]):
    unique_ids = set(sales_rep_ids or [])
    reps = SalesRepresentative.objects.filter(company=company, id__in=unique_ids)
    if reps.count() != len(unique_ids):
        return None
    return reps


def _validate_colony_ids(company: Company, colony_ids: list[int]):
    unique_ids = set(colony_ids or [])
    colonies = Colony.objects.filter(colony_owner=company, id__in=unique_ids)
    if colonies.count() != len(unique_ids):
        return None
    return colonies


def create_customer_with_user(company: Company, validated_data: dict) -> dict:
    sales_rep_ids = validated_data.get("assigned_sales_rep_ids", [])
    colony_ids = validated_data.get("colony_ids", [])

    valid_sales_reps = _validate_sales_rep_ids(company, sales_rep_ids)
    if valid_sales_reps is None:
        return {"success": False, "message": "One or more sales representatives are invalid for this company."}

    valid_colonies = _validate_colony_ids(company, colony_ids)
    if valid_colonies is None:
        return {"success": False, "message": "One or more colonies are invalid for this company."}

    try:
        with transaction.atomic():
            password = 'securePass123'
            user = User.objects.create_user(
                email=validated_data.get("email_address"),
                password=password,
                full_name=validated_data.get("company_owner_name", ""),
                phone=validated_data.get("phone_number") or None,
                role="user",
                is_email_verified=True,
                is_phone_verified=True,
            )

            customer_payload = {
                model_field: validated_data.get(input_field)
                for input_field, model_field in CUSTOMER_FIELD_MAPPING.items()
                if input_field in validated_data
            }
            customer_payload["owner_company"] = company
            customer_payload["user"] = user
            customer_payload["status"] = "active"

            

            customer = Customer.objects.create(**customer_payload)

            if sales_rep_ids:
                customer.sales_reps.set(valid_sales_reps)

            assigned_colonies_count = 0
            if colony_ids:
                for colony in valid_colonies:
                    colony.customers.add(customer)
                assigned_colonies_count = valid_colonies.count()

            return {
                "success": True,
                "customer": customer,
                "assigned_sales_reps_count": len(set(sales_rep_ids)),
                "assigned_colonies_count": assigned_colonies_count,
                "machinery_info_accepted": "machinery_info" in validated_data,
                "message": "Customer created successfully.",
            }
    except Exception as exc:
        return {"success": False, "message": str(exc)}


def update_customer(customer_id: int, company: Company, validated_data: dict) -> dict:
    customer = get_customer_by_id(customer_id, company)
    if not customer:
        return {"success": False, "message": "Customer not found.", "status": "not_found"}

    sales_rep_ids = validated_data.get("assigned_sales_rep_ids")
    colony_ids = validated_data.get("colony_ids")

    if sales_rep_ids is not None:
        valid_sales_reps = _validate_sales_rep_ids(company, sales_rep_ids)
        if valid_sales_reps is None:
            return {"success": False, "message": "One or more sales representatives are invalid for this company."}
    else:
        valid_sales_reps = None

    if colony_ids is not None:
        valid_colonies = _validate_colony_ids(company, colony_ids)
        if valid_colonies is None:
            return {"success": False, "message": "One or more colonies are invalid for this company."}
    else:
        valid_colonies = None

    try:
        with transaction.atomic():
            for input_field, model_field in CUSTOMER_FIELD_MAPPING.items():
                if input_field in validated_data:
                    setattr(customer, model_field, validated_data.get(input_field))
            customer.save()

            if customer.user:
                if "company_owner_name" in validated_data:
                    customer.user.full_name = validated_data.get("company_owner_name")
                if "email_address" in validated_data:
                    customer.user.email = validated_data.get("email_address")
                if "phone_number" in validated_data:
                    customer.user.phone = validated_data.get("phone_number")
                customer.user.save()

            if sales_rep_ids is not None:
                customer.sales_reps.set(valid_sales_reps)

            if colony_ids is not None:
                customer.colonies.clear()
                if colony_ids:
                    for colony in valid_colonies:
                        colony.customers.add(customer)

            return {
                "success": True,
                "customer": customer,
                "assigned_sales_reps_count": customer.sales_reps.count(),
                "assigned_colonies_count": customer.colonies.count(),
                "message": "Customer updated successfully.",
            }
    except Exception as exc:
        return {"success": False, "message": str(exc)}


def delete_customer(customer_id: int, company: Company) -> bool:
    customer = Customer.objects.filter(id=customer_id, owner_company=company).select_related("user").first()
    if not customer:
        return False

    with transaction.atomic():
        linked_user = customer.user
        customer.delete()
        if linked_user:
            linked_user.delete()

    return True
