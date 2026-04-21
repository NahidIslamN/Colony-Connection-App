import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.admin_dashboard.selectors import get_terms_condition_by_id, get_terms_conditions_queryset
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

    def get(self, request, pk=None):
        if pk is not None:
            terms_condition = get_terms_condition_by_id(pk)
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

        terms_conditions = get_terms_conditions_queryset()
        serializer = TermsConditionSerializer(terms_conditions, many=True)
        return success_response(
            "Terms and conditions fetched successfully.",
            status_code=status.HTTP_200_OK,
            data=serializer.data,
        )
    



class TermsConditionAdminView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request, pk=None):
        if pk is not None:
            terms_condition = get_terms_condition_by_id(pk)
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

        queryset = get_terms_conditions_queryset()
        paginator = CustomPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = TermsConditionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = TermsConditionSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            terms_condition = create_terms_condition(serializer.validated_data)
            output_serializer = TermsConditionSerializer(terms_condition)
            return success_response(
                "Terms and conditions created successfully.",
                status_code=status.HTTP_201_CREATED,
                data=output_serializer.data,
            )
        except TermsConditionServiceError as exc:
            return error_response(
                "Failed to create terms and conditions.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={"detail": exc.details or exc.code},
            )
        except Exception:
            logger.exception("Unhandled error while creating terms and conditions")
            return error_response(
                "Failed to create terms and conditions.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"detail": "An unexpected server error occurred."},
            )

    def patch(self, request, pk=None):
        if pk is None:
            return error_response(
                "Failed to update terms and conditions.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={"detail": "Terms and conditions id is required."},
            )

        serializer = TermsConditionSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            terms_condition = update_terms_condition(pk, serializer.validated_data)
            output_serializer = TermsConditionSerializer(terms_condition)
            return success_response(
                "Terms and conditions updated successfully.",
                status_code=status.HTTP_200_OK,
                data=output_serializer.data,
            )
        except TermsConditionServiceError as exc:
            status_code = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
            return error_response(
                "Failed to update terms and conditions.",
                status_code=status_code,
                errors={"detail": exc.details or exc.code},
            )
        except Exception:
            logger.exception("Unhandled error while updating terms and conditions")
            return error_response(
                "Failed to update terms and conditions.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"detail": "An unexpected server error occurred."},
            )

    def put(self, request, pk=None):
        return self.patch(request=request, pk=pk)

    def delete(self, request, pk=None):
        if pk is None:
            return error_response(
                "Failed to delete terms and conditions.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={"detail": "Terms and conditions id is required."},
            )

        try:
            delete_terms_condition(pk)
            return success_response(
                "Terms and conditions deleted successfully.",
                status_code=status.HTTP_200_OK,
                data={"deleted": True, "id": pk},
            )
        except TermsConditionServiceError as exc:
            status_code = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
            return error_response(
                "Failed to delete terms and conditions.",
                status_code=status_code,
                errors={"detail": exc.details or exc.code},
            )
        except Exception:
            logger.exception("Unhandled error while deleting terms and conditions")
            return error_response(
                "Failed to delete terms and conditions.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"detail": "An unexpected server error occurred."},
            )




        



