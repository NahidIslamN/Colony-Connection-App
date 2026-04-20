import logging

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.managements.serializers.input import SupportMessageCreateInputSerializer
from apps.managements.serializers.output import SupportMessageOutputSerializer
from apps.managements.services import create_support_message
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)


class SupportMessageCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        uploaded_files = request.FILES.getlist("files")
        if uploaded_files:
            data.setlist("files", uploaded_files)

        serializer = SupportMessageCreateInputSerializer(data=data)
        if not serializer.is_valid():
            return error_response(
                "Validation error.",
                status.HTTP_400_BAD_REQUEST,
                errors=serializer.errors,
            )

        try:
            support_message = create_support_message(serializer.validated_data)
            output_serializer = SupportMessageOutputSerializer(support_message)
            return success_response(
                "Support message sent successfully.",
                status.HTTP_201_CREATED,
                data=output_serializer.data,
            )
        except Exception as exc:
            logger.error(f"Error creating support message: {exc}", exc_info=True)
            return error_response(
                "Failed to send support message.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
