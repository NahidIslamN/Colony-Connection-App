import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.admin_dashboard.selectors import get_terms_condition_by_id, get_terms_conditions_queryset,get_terms_condition
from apps.admin_dashboard.serializers import TermsConditionSerializer
from apps.admin_dashboard.services import (
    TermsConditionServiceError,
    create_terms_condition,
    delete_terms_condition,
    update_terms_condition,
)
from core.custom_permission import IsAdmin
from core.pagination import CustomPagination

from core.responses import error_response, success_response

logger = logging.getLogger(__name__)



class TermsConditionPublicView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        
        terms_condition = get_terms_condition()
        if not terms_condition:
            return error_response(
                "Terms and conditions not found.",
                status_code=status.HTTP_404_NOT_FOUND,
                errors={"detail": "Requested terms and conditions item does not exist."},
            )

        serializer = TermsConditionSerializer(terms_condition)
        return success_response(
            "Terms and conditions fetched successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )

        

class TermsConditionAdminView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        
        terms_condition = get_terms_condition()
        if not terms_condition:
            return error_response(
                "Terms and conditions not found.",
                status_code=status.HTTP_404_NOT_FOUND,
                errors={"detail": "Requested terms and conditions item does not exist."},
            )

        serializer = TermsConditionSerializer(terms_condition)
        return success_response(
            "Terms and conditions fetched successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )



    def patch(self, request, pk=None):
        terms_condition = get_terms_condition()
        serializer = TermsConditionSerializer(instance = terms_condition, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )
        
        serializer.save()

        return success_response(
            "Terms and conditions fetched successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )



        



