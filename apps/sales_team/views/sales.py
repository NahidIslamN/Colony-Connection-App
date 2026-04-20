import logging

from django.db import transaction
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.sales_team.serializers.input import VisitColonyReportQueryInputSerializer
from apps.sales_team.serializers.output import VisitColonyReportOutputSerializer
from apps.sales_team.services import get_sales_rep_for_user, get_visit_colony_reports_for_sales_rep
from core.custom_permission import IsSalesRep
from core.pagination import CustomPagination
from core.responses import error_response

logger = logging.getLogger(__name__)


class VisitColonyReport_SpecificDay(APIView):
    permission_classes = [IsSalesRep]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]

    def get(self, request):
        serializer = VisitColonyReportQueryInputSerializer(data=request.query_params)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        sales_rep = get_sales_rep_for_user(request.user)
        if not sales_rep:
            return error_response(
                "Sales representative profile not found.",
                status.HTTP_404_NOT_FOUND,
            )

        try:
            report_date = serializer.validated_data["date"]
            with transaction.atomic():
                report_queryset = get_visit_colony_reports_for_sales_rep(sales_rep, report_date)

            paginator = CustomPagination()
            page = paginator.paginate_queryset(report_queryset, request)
            output_serializer = VisitColonyReportOutputSerializer(page, many=True)
            return paginator.get_paginated_response(output_serializer.data)
        except Exception as exc:
            logger.error(f"Error fetching visit colony report: {exc}", exc_info=True)
            return error_response(
                "Failed to fetch visit colony report.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



