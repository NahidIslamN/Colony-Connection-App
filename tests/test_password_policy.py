from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.auths.models import CustomUser


@override_settings(SECURE_SSL_REDIRECT=False)
class PasswordPolicyTests(APITestCase):
    signup_endpoint = "/api/v1/auth/signup"
    reset_endpoint = "/api/v1/auth/reset-password"

    def setUp(self):
        self.user = CustomUser.objects.create_user(email="secure@example.com", password="StrongPass123!")

    def test_signup_rejects_weak_password(self):
        response = self.client.post(
            self.signup_endpoint,
            {
                "full_name": "Weak User",
                "email": "weak-user@example.com",
                "password": "1234",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Password does not meet security requirements.")
        self.assertIn("errors", response.data)

    def test_reset_password_rejects_weak_password(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.reset_endpoint, {"new_password": "1234"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(response.data["message"], "Password does not meet security requirements.")
        self.assertIn("errors", response.data)
