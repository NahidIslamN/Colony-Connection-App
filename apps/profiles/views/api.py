from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.profiles.serializers.input import MyAccountPatchInputSerializer
from apps.profiles.serializers.output import CustomUserOutputSerializer
from apps.profiles.services.profile_service import update_my_account
from core.responses import error_response, success_response


class MyAccountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        serializer = CustomUserOutputSerializer(request.user)
        return success_response("data fetched successfully!", status.HTTP_200_OK, data=serializer.data)

    def patch(self, request):
        serializer = MyAccountPatchInputSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response("validation errors!", status.HTTP_400_BAD_REQUEST, errors=serializer.errors)

        updated_user = update_my_account(request.user, dict(serializer.validated_data))
        output = CustomUserOutputSerializer(updated_user)
        return success_response("Profile partially updated", status.HTTP_200_OK, data=output.data)
