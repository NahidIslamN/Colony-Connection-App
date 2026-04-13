import base64

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from common.file_validation import (
    MAX_PROFILE_IMAGE_SIZE_BYTES,
    decode_and_validate_base64_file,
    validate_uploaded_file,
    validate_uploaded_image,
)
from core.exceptions import ValidationDomainError


class FileValidationTests(SimpleTestCase):
    def test_accepts_valid_png_upload(self):
        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
        file_obj = SimpleUploadedFile("image.png", png_bytes, content_type="image/png")

        validate_uploaded_file(file_obj)

    def test_rejects_spoofed_extension(self):
        fake_jpg = b"not-a-real-jpeg-content"
        file_obj = SimpleUploadedFile("image.jpg", fake_jpg, content_type="image/jpeg")

        with self.assertRaises(ValidationDomainError):
            validate_uploaded_file(file_obj)

    def test_rejects_invalid_base64_payload(self):
        payload = "data:image/png;base64," + base64.b64encode(b"not-a-png").decode()

        with self.assertRaises(ValidationDomainError):
            decode_and_validate_base64_file(payload)

    def test_rejects_oversized_upload(self):
        large = b"\x89PNG\r\n\x1a\n" + (b"\x00" * (10 * 1024 * 1024 + 1))
        file_obj = SimpleUploadedFile("large.png", large, content_type="image/png")
        with self.assertRaises(ValidationDomainError):
            validate_uploaded_file(file_obj)

    def test_rejects_oversized_profile_image(self):
        large = b"\x89PNG\r\n\x1a\n" + (b"\x00" * (MAX_PROFILE_IMAGE_SIZE_BYTES + 1))
        file_obj = SimpleUploadedFile("avatar.png", large, content_type="image/png")
        with self.assertRaises(ValidationDomainError):
            validate_uploaded_image(file_obj)

    def test_rejects_non_image_profile_upload(self):
        payload = b"%PDF-1.7\n"
        file_obj = SimpleUploadedFile("avatar.pdf", payload, content_type="application/pdf")
        with self.assertRaises(ValidationDomainError):
            validate_uploaded_image(file_obj)
