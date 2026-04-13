from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.auths.models import CustomUser
from apps.profiles.services.profile_service import update_my_account
from common.file_validation import MAX_PROFILE_IMAGE_SIZE_BYTES
from core.exceptions import ValidationDomainError


class ProfileSecurityTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email="profile@example.com", password="StrongPass123!")

    def test_update_profile_rejects_oversized_image(self):
        large_image = b"\x89PNG\r\n\x1a\n" + (b"\x00" * (MAX_PROFILE_IMAGE_SIZE_BYTES + 1))
        uploaded = SimpleUploadedFile("avatar.png", large_image, content_type="image/png")

        with self.assertRaises(ValidationDomainError):
            update_my_account(self.user, {"image": uploaded})
