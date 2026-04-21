import logging

from django.db import IntegrityError
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.admin_dashboard.serializers import (
    CompanyManagementInputSerializer,
    CompanyManagementOutputSerializer,
    CompanyManagementUpdateInputSerializer,
    AdminSupportMessageSerializers,
)
from apps.admin_dashboard.services import (
    CompanyServiceError,
    create_company,
    delete_company,
    get_company_by_id,
    list_companies,
    update_company,
    list_support_messages,
)
from core.custom_permission import IsAdmin
from core.pagination import CustomPagination
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)



class SupportMessageAdminView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        keyword = request.GET.get("search")
        queryset = list_support_messages(keyword=keyword)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AdminSupportMessageSerializers(page, many=True)
        return paginator.get_paginated_response(serializer.data)






class CompanyManagementAdminView(APIView):
    permission_classes = [IsAdmin]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def _not_found(self):
        return error_response(
            "Company not found.",
            status_code=status.HTTP_404_NOT_FOUND,
            errors={"detail": "The requested company does not exist."},
        )

    def get(self, request, pk=None):
        if pk is not None:
            company = get_company_by_id(pk)
            if not company:
                return self._not_found()

            return success_response(
                "Company data fetched successfully.",
                status_code=status.HTTP_200_OK,
                data=CompanyManagementOutputSerializer(company).data,
            )

        queryset = list_companies(request.query_params)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = CompanyManagementOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = CompanyManagementInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Company create failed.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = create_company(validate_data=serializer.validated_data)
        except CompanyServiceError as exc:
            status_code = status.HTTP_409_CONFLICT if exc.code == "integrity_error" else status.HTTP_400_BAD_REQUEST
            return error_response(
                "Company create failed.",
                status_code=status_code,
                errors={"detail": exc.details or exc.code},
            )
        except IntegrityError:
            return error_response(
                "Company create failed.",
                status_code=status.HTTP_409_CONFLICT,
                errors={"detail": "Duplicate company or user data found."},
            )
        except Exception:
            logger.exception("Unhandled error while creating company")
            return error_response(
                "Company create failed.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"detail": "An unexpected server error occurred."},
            )

        return success_response(
            "Company created successfully.",
            status_code=status.HTTP_201_CREATED,
            data=CompanyManagementOutputSerializer(company).data,
        )

    def put(self, request, pk=None):
        if pk is None:
            return error_response(
                "Company update failed.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={"detail": "Company id is required."},
            )

        serializer = CompanyManagementUpdateInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                "Company update failed.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            company = update_company(company_id=pk, validate_data=serializer.validated_data)
        except CompanyServiceError as exc:
            if exc.code == "company_not_found":
                status_code = status.HTTP_404_NOT_FOUND
            elif exc.code == "integrity_error":
                status_code = status.HTTP_409_CONFLICT
            else:
                status_code = status.HTTP_400_BAD_REQUEST
            return error_response(
                "Company update failed.",
                status_code=status_code,
                errors={"detail": exc.details or exc.code},
            )
        except IntegrityError:
            return error_response(
                "Company update failed.",
                status_code=status.HTTP_409_CONFLICT,
                errors={"detail": "Duplicate company or user data found."},
            )
        except Exception:
            logger.exception("Unhandled error while updating company")
            return error_response(
                "Company update failed.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"detail": "An unexpected server error occurred."},
            )

        return success_response(
            "Company updated successfully.",
            status_code=status.HTTP_200_OK,
            data=CompanyManagementOutputSerializer(company).data,
        )

    def patch(self, request, pk=None):
        return self.put(request=request, pk=pk)

    def delete(self, request, pk=None):
        if pk is None:
            return error_response(
                "Company delete failed.",
                status_code=status.HTTP_400_BAD_REQUEST,
                errors={"detail": "Company id is required."},
            )

        try:
            delete_company(company_id=pk)
        except CompanyServiceError as exc:
            return error_response(
                "Company delete failed.",
                status_code=status.HTTP_404_NOT_FOUND,
                errors={"detail": exc.details or exc.code},
            )
        except Exception:
            logger.exception("Unhandled error while deleting company")
            return error_response(
                "Company delete failed.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"detail": "An unexpected server error occurred."},
            )

        return success_response(
            "Company deleted successfully.",
            status_code=status.HTTP_200_OK,
            data={"deleted": True, "company_id": pk},
        )