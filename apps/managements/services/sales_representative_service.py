from apps.managements.models import Company, SalesRepresentative, Colony
from django.contrib.auth import get_user_model
from django.db.models import Count, Q

User = get_user_model()


def get_sales_reps_for_company(company: Company):
    return SalesRepresentative.objects.filter(company=company).select_related("user").prefetch_related("colonies")


def get_sales_reps_with_performance(company: Company, recent_days: int = 30):
    """Return sales reps queryset annotated with performance-related counts.

    Annotations added:
    - assigned_colonies_count
    - assigned_customers_count
    - completed_customers_count
    - recent_completed_count (completed customers in the last `recent_days` days)

    These annotations avoid N+1 queries so the view can compute a
    stable performance_score per rep in a single query.
    """
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.localdate()
    recent_threshold = today - timedelta(days=recent_days - 1)

    qs = (
        SalesRepresentative.objects.filter(company=company)
        .select_related("user")
        .annotate(
            assigned_colonies_count=Count("colonies", distinct=True),
            assigned_customers_count=Count("colonies__customers", distinct=True),
            completed_customers_count=Count("colonies__visitcolony__completed_customers", distinct=True),
            recent_completed_count=Count(
                "colonies__visitcolony__completed_customers",
                filter=Q(colonies__visitcolony__date__gte=recent_threshold),
                distinct=True,
            ),
        )
    )

    return qs


def get_sales_rep_by_id(sales_rep_id: int, company: Company):
    return (
        SalesRepresentative.objects.filter(id=sales_rep_id, company=company)
        .select_related("user")
        .prefetch_related("colonies")
        .first()
    )


def create_sales_rep_with_user(company: Company, validated_data: dict) -> dict:
    """
    Create a new User, then create a SalesRepresentative with that user,
    and optionally assign colonies.
    
    Args:
        company: Company instance for scoping
        validated_data: dict containing:
            - email: user email
            - full_name: user full name
            - phone: user phone
            - password: user password
            - status: sales rep status
            - colony_ids: (optional) list of colony IDs to assign
    
    Returns:
        dict with success status, user, sales_rep, and assigned_colonies_count
    """
    try:
        # Step 1: Create User
        user = User.objects.create_user(
            email=validated_data.get('email'),
            full_name=validated_data.get('full_name'),
            phone=validated_data.get('phone'),
            is_email_verified=True,
            is_phone_verified=True
        )

        user.set_password(validated_data.get('password'))
        user.save()
        
        # Step 2: Create SalesRepresentative
        sales_rep = SalesRepresentative.objects.create(
            company=company,
            user=user,
            full_name=validated_data.get('full_name'),
            status=validated_data.get('status', 'inactive'),
            email=validated_data.get('email'),
            phone=validated_data.get('phone')
        )
        
        # Step 3: Assign colonies if provided
        assigned_colonies_count = 0
        colony_ids = validated_data.get('colony_ids', [])
        
        if colony_ids:
            colonies = Colony.objects.filter(id__in=colony_ids, colony_owner=company)
            for colony in colonies:
                colony.sales_reps.add(sales_rep)
            assigned_colonies_count = colonies.count()
        
        return {
            "success": True,
            "user": user,
            "sales_rep": sales_rep,
            "assigned_colonies_count": assigned_colonies_count,
            "message": f"Sales Representative created successfully and assigned to {assigned_colonies_count} colonies"
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "error": str(e)
        }




def update_sales_rep(sales_rep_id: int, company: Company, validated_data: dict) -> SalesRepresentative:
    sales_rep = get_sales_rep_by_id(sales_rep_id, company)
    if not sales_rep:
        return None

    for key, value in validated_data.items():
        setattr(sales_rep, key, value)
    sales_rep.save()
    return sales_rep


def delete_sales_rep(sales_rep_id: int, company: Company) -> bool:
    sales_rep = get_sales_rep_by_id(sales_rep_id, company)
    if not sales_rep:
        return False

    sales_rep.delete()
    return True


def assign_sales_rep_to_colonies(sales_rep_id: int, company: Company, colony_ids: list) -> dict:
    """
    Assign a sales representative to multiple colonies.
    
    Args:
        sales_rep_id: ID of the sales representative
        company: Company instance for scoping
        colony_ids: List of colony IDs to assign to
    
    Returns:
        dict with success status and details
    """
    sales_rep = get_sales_rep_by_id(sales_rep_id, company)
    if not sales_rep:
        return {"success": False, "message": "Sales Representative not found"}
    
    # Get all colonies for the company
    colonies = Colony.objects.filter(id__in=colony_ids, colony_owner=company)
    
    if not colonies.exists():
        return {"success": False, "message": "No valid colonies found"}
    
    # Add sales rep to these colonies
    for colony in colonies:
        colony.sales_reps.add(sales_rep)
    
    return {
        "success": True,
        "message": f"Sales Representative assigned to {colonies.count()} colonies",
        "assigned_colonies_count": colonies.count(),
        "total_requested": len(colony_ids)
    }


def get_colonies_for_sales_rep(sales_rep_id: int, company: Company):
    """Get all colonies assigned to a sales representative."""
    sales_rep = get_sales_rep_by_id(sales_rep_id, company)
    if not sales_rep:
        return None
    
    return sales_rep.colonies.all()
