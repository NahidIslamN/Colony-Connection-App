import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.managements.models import Company
from apps.managements.serializers.input import ColonyCreateUpdateInputSerializer, ColonyPatchInputSerializer
from apps.managements.serializers.output import ColonyOutputSerializer
from apps.managements.services import (
    create_colony,
    delete_colony,
    get_colonies_for_company,
    get_colony_by_id,
    update_colony,
)
from core.custom_permission import IsCompany
from core.pagination import CustomPagination
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)


class ColonyListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsCompany]
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
    permission_classes = [IsAuthenticated, IsCompany]
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

    def put(self, request, pk):
        serializer = ColonyCreateUpdateInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = Company.objects.get(user=request.user)
            colony = update_colony(pk, company, serializer.validated_data)
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