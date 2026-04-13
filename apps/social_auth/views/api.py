import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.auths.serializers.output import AuthenticatedUserOutputSerializer
from apps.auths.services.auth_service import build_jwt_payload
from apps.social_auth.serializers.input import GoogleLoginInputSerializer
from apps.social_auth.services.auth_service import AuthServiceError, google_login
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=24 * 60 * 60 * 30,
    )


class GoogleLoginView(APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = GoogleLoginInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Invalid Google token", status.HTTP_400_BAD_REQUEST, errors=serializer.errors)

        try:
            user = google_login(serializer.validated_data["id_token"])
        except AuthServiceError as exc:
            logger.warning("Google login rejected")
            if exc.code == "google_oauth_misconfigured":
                return error_response(
                    "Google authentication is temporarily unavailable.",
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            return error_response("Invalid Google token", status.HTTP_400_BAD_REQUEST)

        token_payload = build_jwt_payload(user)
        user_data = AuthenticatedUserOutputSerializer(user).data
        response = success_response(
            "login successful!",
            status.HTTP_200_OK,
            data={"access": token_payload["access"], "user": user_data},
        )
        _set_refresh_cookie(response, token_payload["refresh"])
        logger.info("Google login successful", extra={"user_id": user.id})
        return response
