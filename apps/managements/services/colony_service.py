"""
Colony business logic service layer.
"""

from apps.managements.models import Colony, Company


def get_colonies_for_company(company: Company):
    """Get all colonies for a specific company."""
    return Colony.objects.filter(colony_owner=company)


def get_colony_by_id(colony_id: int, company: Company):
    """Get a single colony by ID, ensuring it belongs to the company."""
    return Colony.objects.filter(id=colony_id, colony_owner=company).first()


def create_colony(company: Company, validated_data: dict) -> Colony:
    """Create a new colony for a company."""
    sales_reps = validated_data.pop("sales_reps", None)
    customers = validated_data.pop("customers", None)

    colony = Colony.objects.create(colony_owner=company, **validated_data)

    if sales_reps is not None:
        colony.sales_reps.set(sales_reps)
    if customers is not None:
        colony.customers.set(customers)

    return colony


def update_colony(colony_id: int, company: Company, validated_data: dict, partial: bool = False) -> Colony:
    """Update a colony, ensuring it belongs to the company."""
    colony = Colony.objects.filter(id=colony_id, colony_owner=company).first()
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

    return colony


def delete_colony(colony_id: int, company: Company) -> bool:
    """Delete a colony, ensuring it belongs to the company."""
    colony = Colony.objects.filter(id=colony_id, colony_owner=company).first()
    if not colony:
        return False
    colony.delete()
    return True
