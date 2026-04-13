from django.urls import path

from apps.auths.views.auth import (
    ChangePasswordView,
    ForgetPasswordView,
    LoginView,
    RefreshTokenView,
    ResetPasswordView,
    SignupView,
    VerifyEmailSignupView,
    VerifyForgetPasswordUserView,
)

urlpatterns = [
    path("signup", SignupView.as_view(), name="signup"),
    path("email-verify", VerifyEmailSignupView.as_view(), name="email-verify"),
    path("login", LoginView.as_view(), name="login"),
    path("change-password", ChangePasswordView.as_view(), name="change_password"),
    path("forget-password", ForgetPasswordView.as_view(), name="forget_password"),
    path("otp-verify", VerifyForgetPasswordUserView.as_view(), name="verify_user_forget_password"),
    path("reset-password", ResetPasswordView.as_view(), name="reset_password"),
    path("refresh", RefreshTokenView.as_view(), name="refresh_token"),
]
