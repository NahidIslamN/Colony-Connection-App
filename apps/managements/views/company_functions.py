import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.managements.models import Company, Colony,SubscribePlan
from apps.managements.serializers.input import (
    CustomerCreateUpdateInputSerializer,
    CustomerPatchInputSerializer,
    ColonyCreateUpdateInputSerializer,
    ColonyPatchInputSerializer,
    SalesRepresentativeCreateUpdateInputSerializer,
    SalesRepresentativePatchInputSerializer,
    AssignSalesRepToColoniesInputSerializer,
    GetColoniesForSalesRepOutputSerializer,
)
from apps.managements.serializers.output import (
    ColonyOutputSerializer,
    CustomerReadOutputSerializer,
    SalesRepresentativeOutputSerializer,
    SalesRepresentativeReadOutputSerializer,
    SubscriptionPlanOutputSerializer,
)
from apps.managements.services import (
    create_customer_with_user,
    create_colony,

    create_sales_rep_with_user,
    delete_customer,
    delete_colony,
    delete_sales_rep,
    get_colonies_for_company,
    get_colonies_count_for_company,
    get_customer_by_id,
    get_customers_for_company,
    get_total_customer_count_for_company,
    get_active_colonies_count_for_company,
    get_colony_by_id,
    get_sales_rep_by_id,
    get_sales_reps_for_company,
    get_sales_reps_with_performance,
    update_customer,
    update_colony,
    update_sales_rep,
    assign_sales_rep_to_colonies,
    get_colonies_for_sales_rep,
)
from core.custom_permission import IsCompany
from core.pagination import CustomPagination
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)


class ColonyListCreateAPIView(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            company = Company.objects.get(user=request.user)
            colonies = get_colonies_for_company(company)
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)

        paginator = self.pagination_class()
        paginated_colonies = paginator.paginate_queryset(colonies, request)
        serializer = ColonyOutputSerializer(paginated_colonies, many=True)
        return paginator.get_paginated_response(serializer.data)
    

    def post(self, request):
        serializer = ColonyCreateUpdateInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = Company.objects.get(user=request.user)
            colony = create_colony(company, serializer.validated_data)
            output_serializer = ColonyOutputSerializer(colony)
            return success_response(
                "Colony created successfully.",
                status.HTTP_201_CREATED,
                data=output_serializer.data,
            )
        except Company.DoesNotExist:
            return error_response(
                "Company not found for this user.",
                status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error(f"Error creating colony: {exc}", exc_info=True)
            return error_response(
                "Failed to create colony.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        


class ColonyDetailAPIView(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, pk):
        try:
            company = Company.objects.get(user=request.user)
            colony = get_colony_by_id(pk, company)
            if not colony:
                return error_response(
                    "Colony not found.",
                    status.HTTP_404_NOT_FOUND,
                )
            serializer = ColonyOutputSerializer(colony)
            return success_response(
                "Colony retrieved successfully.",
                status.HTTP_200_OK,
                data=serializer.data,
            )
        except Company.DoesNotExist:
            return error_response(
                "Company not found for this user.",
                status.HTTP_404_NOT_FOUND,
            )


    def patch(self, request, pk):
        serializer = ColonyPatchInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = Company.objects.get(user=request.user)
            colony = update_colony(pk, company, serializer.validated_data, partial=True)
            if not colony:
                return error_response(
                    "Colony not found.",
                    status.HTTP_404_NOT_FOUND,
                )
            output_serializer = ColonyOutputSerializer(colony)
            return success_response(
                "Colony updated successfully.",
                status.HTTP_200_OK,
                data=output_serializer.data,
            )
        except Company.DoesNotExist:
            return error_response(
                "Company not found for this user.",
                status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error(f"Error updating colony: {exc}", exc_info=True)
            return error_response(
                "Failed to update colony.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, pk):
        try:
            company = Company.objects.get(user=request.user)
            success = delete_colony(pk, company)
            if not success:
                return error_response(
                    "Colony not found.",
                    status.HTTP_404_NOT_FOUND,
                )
            return success_response(
                "Colony deleted successfully.",
                status.HTTP_204_NO_CONTENT,
            )
        except Company.DoesNotExist:
            return error_response(
                "Company not found for this user.",
                status.HTTP_404_NOT_FOUND,
            )
        except Exception as exc:
            logger.error(f"Error deleting colony: {exc}", exc_info=True)
            return error_response(
                "Failed to delete colony.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    

class ColonyAnalyticsService(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            company = Company.objects.get(user=request.user)

            total_colonies = get_colonies_count_for_company(company)
            total_active_colonies = get_active_colonies_count_for_company(company)
            total_customers = get_total_customer_count_for_company(company)

            data = {
                "total_colonies": total_colonies,
                "total_active_colonies": total_active_colonies,
                "total_customers": total_customers,
            }

            return success_response(
                message="Company analytics retrieved successfully.",
                status_code=status.HTTP_200_OK,
                data=data
            )
        
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)




class SalseRepList(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            company = Company.objects.get(user=request.user)

            # use optimized annotated queryset to include counters for performance calculation
            sales_reps = get_sales_reps_with_performance(company)

        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(sales_reps, request)
        serializer = SalesRepresentativeReadOutputSerializer(page, many=True)

        # enrich serialized data with an optimized `performance_score` computed from annotations
        serialized = serializer.data
        enriched = []
        for idx, rep in enumerate(page):
            item = serialized[idx].copy()
            # read annotation counts (defaults to 0)
            assigned_customers = int(getattr(rep, 'assigned_customers_count', 0) or 0)
            completed_customers = int(getattr(rep, 'completed_customers_count', 0) or 0)
            recent_completed = int(getattr(rep, 'recent_completed_count', 0) or 0)

            # performance_score: primary metric = completed / assigned_customers
            if assigned_customers <= 0:
                score = 0
            else:
                score = round((completed_customers / assigned_customers) * 100)

            # small recent activity bonus (up to +10 points)
            if assigned_customers > 0:
                recent_bonus = min(10, round((recent_completed / max(1, assigned_customers)) * 10))
                score = min(100, score + recent_bonus)

            item['performance_score'] = int(score)
            item['assigned_colonies_count'] = int(getattr(rep, 'assigned_colonies_count', 0) or 0)
            item['assigned_customers_count'] = assigned_customers
            item['completed_customers_count'] = completed_customers
            enriched.append(item)

        return paginator.get_paginated_response(enriched)


#################################### Sale Rep Managements Views #####################


class SalesRepresentativeListCreateAPIView(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            company = Company.objects.get(user=request.user)
            sales_reps = get_sales_reps_for_company(company)
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)

        paginator = self.pagination_class()
        paginated_sales_reps = paginator.paginate_queryset(sales_reps, request)
        serializer = SalesRepresentativeReadOutputSerializer(paginated_sales_reps, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = SalesRepresentativeCreateUpdateInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = Company.objects.get(user=request.user)
            
            # Use the new service function that creates user, sales rep, and assigns colonies
            result = create_sales_rep_with_user(company, serializer.validated_data)
            
            if not result.get('success'):
                return error_response(
                    result.get('message'),
                    status.HTTP_400_BAD_REQUEST,
                    errors=result.get('error')
                )
            
            sales_rep = result.get('sales_rep')
            output_serializer = SalesRepresentativeOutputSerializer(sales_rep)
            
            return success_response(
                result.get('message'),
                status.HTTP_201_CREATED,
                data={
                    "sales_representative": output_serializer.data,
                    "assigned_colonies_count": result.get('assigned_colonies_count')
                }
            )
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error creating sales representative: {exc}", exc_info=True)
            return error_response("Failed to create sales representative.", status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesRepresentativeDetailAPIView(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, pk):
        try:
            company = Company.objects.get(user=request.user)
            sales_rep = get_sales_rep_by_id(pk, company)
            if not sales_rep:
                return error_response("Sales representative not found.", status.HTTP_404_NOT_FOUND)

            serializer = SalesRepresentativeReadOutputSerializer(sales_rep)
            return success_response(
                "Sales representative retrieved successfully.",
                status.HTTP_200_OK,
                data=serializer.data,
            )
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        serializer = SalesRepresentativePatchInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = Company.objects.get(user=request.user)
            sales_rep = update_sales_rep(pk, company, serializer.validated_data)
            if not sales_rep:
                return error_response("Sales representative not found.", status.HTTP_404_NOT_FOUND)

            output_serializer = SalesRepresentativeOutputSerializer(sales_rep)
            return success_response(
                "Sales representative updated successfully.",
                status.HTTP_200_OK,
                data=output_serializer.data,
            )
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error updating sales representative: {exc}", exc_info=True)
            return error_response("Failed to update sales representative.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            company = Company.objects.get(user=request.user)
            success = delete_sales_rep(pk, company)
            if not success:
                return error_response("Sales representative not found.", status.HTTP_404_NOT_FOUND)

            return success_response("Sales representative deleted successfully.", status.HTTP_204_NO_CONTENT)
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error deleting sales representative: {exc}", exc_info=True)
            return error_response("Failed to delete sales representative.", status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignSalesRepToColoniesAPIView(APIView):
    """Assign a Sales Representative to multiple colonies."""
    
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def post(self, request, sales_rep_id):
        """Assign a sales rep to colonies."""
        logger.info(f"[REQUEST_ID: {request.request_id}] POST - Assign sales rep {sales_rep_id} to colonies")
        
        serializer = AssignSalesRepToColoniesInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors
            )
        
        try:
            company = Company.objects.get(user=request.user)
            colony_ids = serializer.validated_data.get('colony_ids', [])
            
            result = assign_sales_rep_to_colonies(sales_rep_id, company, colony_ids)
            
            if not result.get('success'):
                return error_response(result.get('message'), status.HTTP_400_BAD_REQUEST)
            
            return success_response(
                result.get('message'),
                status.HTTP_200_OK,
                data={
                    "sales_rep_id": sales_rep_id,
                    "assigned_colonies_count": result.get('assigned_colonies_count'),
                    "total_requested": result.get('total_requested')
                }
            )
        
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error assigning sales rep to colonies: {exc}", exc_info=True)
            return error_response("Failed to assign sales representative to colonies.", status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetSalesRepColoniesAPIView(APIView):
    """Get all colonies assigned to a sales representative."""
    
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    
    pagination_class = CustomPagination

    def get(self, request, sales_rep_id):
        """Get list of colonies for a sales rep."""
        logger.info(f"[REQUEST_ID: {request.request_id}] GET - Colonies for sales rep {sales_rep_id}")
        
        try:
            company = Company.objects.get(user=request.user)
            colonies = get_colonies_for_sales_rep(sales_rep_id, company)
            
            if colonies is None:
                return error_response("Sales Representative not found.", status.HTTP_404_NOT_FOUND)
            
            # Apply pagination
            paginator = self.pagination_class()
            paginated_colonies = paginator.paginate_queryset(colonies, request)
            
            serializer = GetColoniesForSalesRepOutputSerializer(paginated_colonies, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error retrieving colonies for sales rep: {exc}", exc_info=True)
            return error_response("Failed to retrieve colonies.", status.HTTP_500_INTERNAL_SERVER_ERROR)


class ColoniesForAssignmentAPIView(APIView):
    """Get list of colonies available for assignment to sales representatives."""
    
    permission_classes = [IsAuthenticated]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        """Get list of colonies for the company."""
        logger.info(f"[REQUEST_ID: {request.request_id}] GET - Available colonies for assignment")
        
        try:
            company = Company.objects.get(user=request.user)
            colonies = Colony.objects.filter(colony_owner=company).values('id', 'name', 'region', 'status')
            
            return success_response(
                "Colonies retrieved successfully",
                status.HTTP_200_OK,
                data=list(colonies)
            )
        
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error retrieving colonies: {exc}", exc_info=True)
            return error_response("Failed to retrieve colonies.", status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalesRepsForAssignmentAPIView(APIView):
    """Get list of sales reps available for assignment to customers."""

    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        logger.info(f"[REQUEST_ID: {request.request_id}] GET - Available sales reps for assignment")

        try:
            company = Company.objects.get(user=request.user)
            sales_reps = get_sales_reps_for_company(company).values("id", "full_name", "status", "email", "phone")
            return success_response(
                "Sales representatives retrieved successfully",
                status.HTTP_200_OK,
                data=list(sales_reps),
            )
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error retrieving sales representatives: {exc}", exc_info=True)
            return error_response("Failed to retrieve sales representatives.", status.HTTP_500_INTERNAL_SERVER_ERROR)


#################################### Customer Management Views #####################


class CustomerListCreateAPIView(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    pagination_class = CustomPagination

    def get(self, request):
        try:
            company = Company.objects.get(user=request.user)
            customers = get_customers_for_company(company)
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)

        paginator = self.pagination_class()
        paginated_customers = paginator.paginate_queryset(customers, request)
        serializer = CustomerReadOutputSerializer(paginated_customers, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CustomerCreateUpdateInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = Company.objects.get(user=request.user)
            result = create_customer_with_user(company, serializer.validated_data)

            if not result.get("success"):
                return error_response(result.get("message"), status.HTTP_400_BAD_REQUEST)

            customer = result.get("customer")
            output_serializer = CustomerReadOutputSerializer(customer)

            return success_response(
                result.get("message"),
                status.HTTP_201_CREATED,
                data={
                    "customer": output_serializer.data,
                    "assigned_sales_reps_count": result.get("assigned_sales_reps_count", 0),
                    "assigned_colonies_count": result.get("assigned_colonies_count", 0),
                    "machinery_info_accepted": result.get("machinery_info_accepted", False),
                },
            )
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error creating customer: {exc}", exc_info=True)
            return error_response("Failed to create customer.", status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerDetailAPIView(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, pk):
        try:
            company = Company.objects.get(user=request.user)
            customer = get_customer_by_id(pk, company)
            if not customer:
                return error_response("Customer not found.", status.HTTP_404_NOT_FOUND)

            serializer = CustomerReadOutputSerializer(customer)
            return success_response(
                "Customer retrieved successfully.",
                status.HTTP_200_OK,
                data=serializer.data,
            )
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        serializer = CustomerPatchInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = Company.objects.get(user=request.user)
            result = update_customer(pk, company, serializer.validated_data)

            if not result.get("success"):
                if result.get("status") == "not_found":
                    return error_response(result.get("message"), status.HTTP_404_NOT_FOUND)
                return error_response(result.get("message"), status.HTTP_400_BAD_REQUEST)

            output_serializer = CustomerReadOutputSerializer(result.get("customer"))
            return success_response(
                result.get("message"),
                status.HTTP_200_OK,
                data={
                    "customer": output_serializer.data,
                    "assigned_sales_reps_count": result.get("assigned_sales_reps_count", 0),
                    "assigned_colonies_count": result.get("assigned_colonies_count", 0),
                },
            )
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error updating customer: {exc}", exc_info=True)
            return error_response("Failed to update customer.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            company = Company.objects.get(user=request.user)
            success = delete_customer(pk, company)
            if not success:
                return error_response("Customer not found.", status.HTTP_404_NOT_FOUND)

            return success_response("Customer deleted successfully.", status.HTTP_204_NO_CONTENT)
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)
        except Exception as exc:
            logger.error(f"Error deleting customer: {exc}", exc_info=True)
            return error_response("Failed to delete customer.", status.HTTP_500_INTERNAL_SERVER_ERROR)




class SubscriptionPlans(APIView):
    permission_classes = [IsCompany]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    def get(self, request):
        try:
            company = Company.objects.select_related("subscription_package").get(user=request.user)
        except Company.DoesNotExist:
            return error_response("Company not found for this user.", status.HTTP_404_NOT_FOUND)

        current_plan = company.subscription_package
        subscription_plans = SubscribePlan.objects.all().order_by("id")

        serializer = SubscriptionPlanOutputSerializer(
            subscription_plans,
            many=True,
            context={"current_plan": current_plan},
        )

        return success_response(
            message="Subscription plans retrieved successfully.",
            status_code=status.HTTP_200_OK,
            data={
                "current_plan": SubscriptionPlanOutputSerializer(
                    current_plan,
                    context={"current_plan": current_plan},
                ).data if current_plan else None,
                "plans": serializer.data,
            },
        )


