import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.auths.serializers.input import (
    ChangePasswordInputSerializer,
    ForgetPasswordInputSerializer,
    LoginInputSerializer,
    OtpInputSerializer,
    ResetPasswordInputSerializer,
    SignupInputSerializer,
)
from apps.auths.serializers.output import AuthenticatedUserOutputSerializer
from apps.auths.services.auth_service import (
    AuthServiceError,
    authenticate_with_password,
    build_jwt_payload,
    change_user_password,
    create_or_update_unverified_signup_user,
    issue_and_send_otp,
    refresh_access_from_refresh_token,
    request_forgot_password_otp,
    reset_user_password,
    verify_forgot_password_otp,
    verify_signup_otp,
)
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


class SignupView(APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = SignupInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("An account with this email already exists.", status.HTTP_400_BAD_REQUEST)

        try:
            user, _ = create_or_update_unverified_signup_user(
                full_name=serializer.validated_data["full_name"],
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
            )
        except AuthServiceError as exc:
            if exc.code == "weak_password":
                return error_response(
                    "Password does not meet security requirements.",
                    status.HTTP_400_BAD_REQUEST,
                    errors=exc.details,
                )
            return error_response("An account with this email already exists.", status.HTTP_400_BAD_REQUEST)

        issue_and_send_otp(user)
        return success_response("Your account has been created successfully.", status.HTTP_201_CREATED)


class VerifyEmailSignupView(APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = OtpInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("validation errors!", status.HTTP_400_BAD_REQUEST, errors=serializer.errors)

        try:
            verify_signup_otp(serializer.validated_data["email"], serializer.validated_data["otp"])
        except AuthServiceError as exc:
            code = str(exc)
            if "expired_otp" in code:
                return error_response(
                    "Your OTP has expired. Please request a new one to verify your email!",
                    status.HTTP_400_BAD_REQUEST,
                )
            if "invalid_otp" in code:
                return error_response("The verification code you entered is incorrect.", status.HTTP_400_BAD_REQUEST)
            return error_response("No account found with the provided email.", status.HTTP_400_BAD_REQUEST)

        return success_response(
            "Your email has been successfully verified. Welcome to Mealz",
            status.HTTP_200_OK,
        )


class LoginView(APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = LoginInputSerializer(data=request.data)
        if not serializer.is_valid():
            error_text = str(next(iter(serializer.errors.values()))[0])
            return error_response(error_text, status.HTTP_400_BAD_REQUEST)

        user = authenticate_with_password(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"],
        )
        if not user:
            logger.warning("Login rejected: invalid credentials", extra={"email": serializer.validated_data["email"]})
            return error_response("username or password Invalid!", status.HTTP_401_UNAUTHORIZED)

        if not user.is_email_verified:
            logger.info("Login blocked: email not verified", extra={"user_id": user.id})
            issue_and_send_otp(user)
            return error_response(
                "We sent an otp to your email! verify your first then login",
                status.HTTP_401_UNAUTHORIZED,
            )

        token_payload = build_jwt_payload(user)
        user_data = AuthenticatedUserOutputSerializer(user).data
        response = success_response(
            "login successful!",
            status.HTTP_200_OK,
            data={"access": token_payload["access"], "user": user_data},
           
        )
        _set_refresh_cookie(response, token_payload["refresh"])
        logger.info("Login successful", extra={"user_id": user.id})
        return response


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = ChangePasswordInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("All fields are required.", status.HTTP_400_BAD_REQUEST)

        try:
            updated = change_user_password(
                user=request.user,
                old_password=serializer.validated_data["old_password"],
                new_password=serializer.validated_data["new_password"],
            )
        except AuthServiceError as exc:
            if exc.code == "weak_password":
                return error_response(
                    "Password does not meet security requirements.",
                    status.HTTP_400_BAD_REQUEST,
                    errors=exc.details,
                )
            return error_response("Unable to change password.", status.HTTP_400_BAD_REQUEST)
        if not updated:
            return error_response(
                "The current password you entered is incorrect. Please try again.",
                status.HTTP_400_BAD_REQUEST,
            )

        return success_response("Your password has been changed successfully.", status.HTTP_200_OK)


class ForgetPasswordView(APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = ForgetPasswordInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("The email field is required.", status.HTTP_400_BAD_REQUEST)

        try:
            request_forgot_password_otp(serializer.validated_data["email"])
        except AuthServiceError:
            logger.warning("Forget password rejected: user not found", extra={"email": serializer.validated_data.get("email")})
            return error_response("No account was found with the provided details.", status.HTTP_400_BAD_REQUEST)

        return success_response("We have sent a verification code (OTP) to your email.", status.HTTP_200_OK)


class VerifyForgetPasswordUserView(APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = OtpInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("The OTP field is required.", status.HTTP_400_BAD_REQUEST)

        try:
            result = verify_forgot_password_otp(serializer.validated_data["email"], serializer.validated_data["otp"])
        except AuthServiceError as exc:
            code = str(exc)
            if "expired_otp" in code:
                return error_response(
                    "Your OTP has expired. Please request a new one to verify your email!",
                    status.HTTP_400_BAD_REQUEST,
                )
            if "invalid_otp" in code:
                return error_response("The verification code you entered is incorrect.", status.HTTP_400_BAD_REQUEST)
            return error_response("No account was found with the provided email.", status.HTTP_400_BAD_REQUEST)

        user = result["user"]
        token_payload = build_jwt_payload(user)
        user_data = AuthenticatedUserOutputSerializer(user).data
        response = success_response(
            "Email verified successfully!",
            status.HTTP_200_OK,
            data={"access": token_payload["access"], "user": user_data},
        )
        _set_refresh_cookie(response, token_payload["refresh"])
        return response


class ResetPasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        serializer = ResetPasswordInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                "Please provide a new password to proceed with resetting your account.",
                status.HTTP_400_BAD_REQUEST,
            )

        try:
            reset_user_password(request.user, serializer.validated_data["new_password"])
        except AuthServiceError as exc:
            if exc.code == "weak_password":
                return error_response(
                    "Password does not meet security requirements.",
                    status.HTTP_400_BAD_REQUEST,
                    errors=exc.details,
                )
            return error_response("Unable to reset password.", status.HTTP_400_BAD_REQUEST)
        return success_response("Your password has been reset successfully.", status.HTTP_200_OK)


class RefreshTokenView(APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        try:
            token_payload = refresh_access_from_refresh_token(refresh_token)
        except AuthServiceError as exc:
            if exc.code == "missing_refresh_token":
                return error_response("Refresh token is required.", status.HTTP_401_UNAUTHORIZED)
            return error_response("Invalid or expired refresh token.", status.HTTP_401_UNAUTHORIZED)

        response = success_response(
            "Token refreshed successfully.",
            status.HTTP_200_OK,
            data={"access": token_payload["access"]},
        )

        if "refresh" in token_payload:
            _set_refresh_cookie(response, token_payload["refresh"])

        return response
