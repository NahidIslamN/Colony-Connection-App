"""
Colony business logic service layer.
"""

from django.db import transaction

from apps.managements.models import Colony, Company, Customer, SalesRepresentative
from apps.managements.services.subscription_limit_service import (
    enforce_colony_creation_allowed,
    enforce_company_active_status_limits,
)


def get_colonies_for_company(company: Company):
    """Get all colonies for a specific company."""
    from django.db.models import Q

    return Colony.objects.filter(
        Q(colony_owner=company) | Q(is_public=True)
    )


def get_colonies_count_for_company(company: Company):
    """Get all colonies for a specific company."""
    return Colony.objects.filter(colony_owner=company).count()


def get_active_colonies_count_for_company(company: Company):
    """Get all colonies for a specific company."""
    return Colony.objects.filter(colony_owner=company, status="active").count()



def get_salses_rep_for_company(company: Company):
    """Get all colonies for a specific company."""
    return SalesRepresentative.objects.filter(company = company)






def get_total_customer_count_for_company(company: Company):
    
    return Customer.objects.filter(owner_company=company).count()



def get_colony_by_id(colony_id: int, company: Company):
    """Get a single colony by ID, ensuring it belongs to the company."""
    return Colony.objects.filter(id=colony_id, colony_owner=company).first()


def create_colony(company: Company, validated_data: dict) -> Colony:
    """Create a new colony for a company."""
    with transaction.atomic():
        locked_company = enforce_colony_creation_allowed(company)

        sales_reps = validated_data.pop("sales_reps", None)
        customers = validated_data.pop("customers", None)

        colony = Colony.objects.create(colony_owner=locked_company, **validated_data)

        if sales_reps is not None:
            colony.sales_reps.set(sales_reps)
        if customers is not None:
            colony.customers.set(customers)

        enforce_company_active_status_limits(locked_company, lock_company=False)
        colony.refresh_from_db()

        return colony


def update_colony(colony_id: int, company: Company, validated_data: dict, partial: bool = False) -> Colony:
    """Update a colony, ensuring it belongs to the company."""
    with transaction.atomic():
        locked_company = enforce_colony_creation_allowed(company)
        colony = Colony.objects.filter(id=colony_id, colony_owner=locked_company).first()
        if not colony:
            return None

        sales_reps = validated_data.pop("sales_reps", None)
        customers = validated_data.pop("customers", None)

        for key, value in validated_data.items():
            setattr(colony, key, value)
        colony.save()

        if sales_reps is not None:
            colony.sales_reps.set(sales_reps)
        if customers is not None:
            colony.customers.set(customers)

        enforce_company_active_status_limits(locked_company, lock_company=False)
        colony.refresh_from_db()
        return colony


def delete_colony(colony_id: int, company: Company) -> bool:
    """Delete a colony, ensuring it belongs to the company."""
    colony = Colony.objects.filter(id=colony_id, colony_owner=company).first()
    if not colony:
        return False
    colony.delete()
    return True
