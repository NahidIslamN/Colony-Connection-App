from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.auths.models import CustomUser
from apps.auths.services.auth_service import build_jwt_payload


@override_settings(SECURE_SSL_REDIRECT=False)
class RefreshTokenApiTests(APITestCase):
    endpoint = "/api/v1/auth/refresh"

    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="refresh-user@example.com",
            password="StrongPass123!",
            full_name="Refresh User",
            is_email_verified=True,
        )

    def test_refresh_returns_new_access_token_from_cookie(self):
        token_payload = build_jwt_payload(self.user)
        self.client.cookies["refresh_token"] = token_payload["refresh"]

        response = self.client.post(self.endpoint, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("request_id", response.data)
        self.assertIn("data", response.data)
        self.assertIn("access", response.data["data"])

    def test_refresh_rejects_missing_refresh_cookie(self):
        response = self.client.post(self.endpoint, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Refresh token is required.")
        self.assertIn("request_id", response.data)

    def test_refresh_rejects_invalid_refresh_cookie(self):
        self.client.cookies["refresh_token"] = "invalid-refresh-token"

        response = self.client.post(self.endpoint, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Invalid or expired refresh token.")
        self.assertIn("request_id", response.data)
