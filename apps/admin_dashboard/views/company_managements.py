import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from apps.managements.models import Company, Colony,SubscribePlan
from core.custom_permission import IsAdmin
from core.pagination import CustomPagination
from core.responses import error_response, success_response
logger = logging.getLogger(__name__)
from apps.admin_dashboard.serializers.input import (
    CompanyManagementInputSerializer
)

## admn views


class CompanyManagementAdminView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        pass

    def post(self, request):
        data = request.data
        
        company_create_serializer = CompanyManagementInputSerializer(data=data)
        if not company_create_serializer.is_valid():
            return error_response(
                "Company Create Failed!",
                status_code=status.HTTP_200_OK,
                errors=company_create_serializer.errors
            )
        
        try:
            pass
        except IntegrityError as interr:
            pass