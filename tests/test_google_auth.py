from unittest.mock import patch

from django.test import override_settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from apps.auths.models import CustomUser
from apps.social_auth.services.auth_service import AuthServiceError


@override_settings(
    GOOGLE_OAUTH_CLIENT_ID="test-google-client-id",
    GOOGLE_OAUTH_CLIENT_IDS=["test-google-client-id"],
    SECURE_SSL_REDIRECT=False,
)
class GoogleAuthFlowTests(APITestCase):
    endpoint = "/api/v1/social_auth/google"

    def setUp(self):
        cache.clear()

    @patch("apps.social_auth.services.auth_service.id_token.verify_oauth2_token")
    def test_google_login_success_with_valid_audience_and_issuer(self, mock_verify):
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "email": "google-user@example.com",
            "email_verified": True,
            "name": "Google User",
        }

        response = self.client.post(self.endpoint, {"id_token": "valid"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("data", response.data)
        self.assertIn("access", response.data["data"])
        self.assertIn("request_id", response.data)
        self.assertTrue(CustomUser.objects.filter(email="google-user@example.com").exists())

        _, kwargs = mock_verify.call_args
        self.assertEqual(kwargs.get("audience"), "test-google-client-id")

    @patch("apps.social_auth.services.auth_service.id_token.verify_oauth2_token")
    def test_google_login_rejects_invalid_token(self, mock_verify):
        mock_verify.side_effect = ValueError("bad token")

        response = self.client.post(self.endpoint, {"id_token": "invalid"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid Google token")
        self.assertIn("request_id", response.data)

    @patch("apps.social_auth.services.auth_service.id_token.verify_oauth2_token")
    def test_google_login_rejects_invalid_issuer(self, mock_verify):
        mock_verify.return_value = {
            "iss": "https://malicious-issuer.example",
            "email": "google-user@example.com",
            "email_verified": True,
            "name": "Google User",
        }

        response = self.client.post(self.endpoint, {"id_token": "invalid-issuer"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    @patch("apps.social_auth.services.auth_service.id_token.verify_oauth2_token")
    def test_google_login_rejects_unverified_email(self, mock_verify):
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "email": "google-user@example.com",
            "email_verified": False,
            "name": "Google User",
        }

        response = self.client.post(self.endpoint, {"id_token": "unverified-email"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    @patch("apps.social_auth.views.api.google_login")
    def test_google_login_maps_service_error_to_400_instead_of_500(self, mock_google_login):
        mock_google_login.side_effect = AuthServiceError("invalid_google_token")

        response = self.client.post(self.endpoint, {"id_token": "invalid"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])

    @override_settings(
        GOOGLE_OAUTH_CLIENT_ID="",
        GOOGLE_OAUTH_CLIENT_IDS=["web-client-id.apps.googleusercontent.com", "android-client-id.apps.googleusercontent.com"],
    )
    @patch("apps.social_auth.services.auth_service.id_token.verify_oauth2_token")
    def test_google_login_accepts_multiple_google_client_ids(self, mock_verify):
        mock_verify.return_value = {
            "iss": "https://accounts.google.com",
            "email": "google-user-2@example.com",
            "email_verified": True,
            "name": "Google User Two",
        }

        response = self.client.post(self.endpoint, {"id_token": "valid"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        _, kwargs = mock_verify.call_args
        self.assertEqual(
            kwargs.get("audience"),
            ["web-client-id.apps.googleusercontent.com", "android-client-id.apps.googleusercontent.com"],
        )

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="", GOOGLE_OAUTH_CLIENT_IDS=[])
    def test_google_login_returns_503_when_google_oauth_not_configured(self):
        response = self.client.post(self.endpoint, {"id_token": "some-token"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(response.data["success"])
