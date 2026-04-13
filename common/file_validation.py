import base64
import binascii
import os
from dataclasses import dataclass

from core.exceptions import ValidationDomainError

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
MAX_PROFILE_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_FILES_PER_MESSAGE = 5

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "gif",
    "pdf",
    "txt",
    "mp3",
    "wav",
    "mp4",
}

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}

ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
    "text/plain",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
}

MIME_TO_EXTENSION = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "application/pdf": "pdf",
    "text/plain": "txt",
    "audio/mpeg": "mp3",
    "audio/wav": "wav",
    "video/mp4": "mp4",
}


@dataclass
class DecodedBase64File:
    content: bytes
    extension: str


def _extract_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename or "")
    return ext.lstrip(".").lower()


def _detect_extension_from_content(data: bytes) -> str | None:
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
        return "gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data.startswith(b"%PDF-"):
        return "pdf"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data.startswith(b"ID3") or (len(data) >= 2 and data[:2] == b"\xff\xfb"):
        return "mp3"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "mp4"

    try:
        data.decode("utf-8")
        return "txt"
    except UnicodeDecodeError:
        return None


def _validate_size(size: int, max_size_bytes: int = MAX_FILE_SIZE_BYTES) -> None:
    if size > max_size_bytes:
        raise ValidationDomainError(code="file_too_large", message="File exceeds size limit")


def _validate_content_match(expected_extension: str, data: bytes) -> None:
    detected = _detect_extension_from_content(data)
    if detected is None:
        raise ValidationDomainError(code="invalid_file_signature", message="File signature is not allowed")

    alias_map = {"jpeg": "jpg"}
    normalized_expected = alias_map.get(expected_extension, expected_extension)
    normalized_detected = alias_map.get(detected, detected)

    if normalized_detected != normalized_expected:
        raise ValidationDomainError(code="invalid_file_signature", message="File content does not match extension")


def validate_uploaded_file(file_obj) -> None:
    content_type = getattr(file_obj, "content_type", "") or ""
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValidationDomainError(code="invalid_file_type", message="Unsupported file type")

    file_size = getattr(file_obj, "size", 0) or 0
    _validate_size(file_size)

    extension = _extract_extension(getattr(file_obj, "name", ""))
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationDomainError(code="invalid_file_extension", message="Unsupported file extension")

    file_obj.seek(0)
    header_bytes = file_obj.read(1024)
    file_obj.seek(0)
    _validate_content_match(extension, header_bytes)


def validate_uploaded_image(file_obj) -> None:
    content_type = getattr(file_obj, "content_type", "") or ""
    if not content_type.startswith("image/"):
        raise ValidationDomainError(code="invalid_file_type", message="Unsupported image type")

    file_size = getattr(file_obj, "size", 0) or 0
    _validate_size(file_size, MAX_PROFILE_IMAGE_SIZE_BYTES)

    extension = _extract_extension(getattr(file_obj, "name", ""))
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationDomainError(code="invalid_file_extension", message="Unsupported image extension")

    file_obj.seek(0)
    header_bytes = file_obj.read(1024)
    file_obj.seek(0)
    _validate_content_match(extension, header_bytes)


def validate_file_batch(files_count: int) -> None:
    if files_count > MAX_FILES_PER_MESSAGE:
        raise ValidationDomainError(code="too_many_files", message="Too many files in one message")


def decode_and_validate_base64_file(file_base64: str) -> DecodedBase64File:
    try:
        format_part, encoded_data = file_base64.split(";base64,", 1)
        mime_type = format_part.split(":", 1)[1].strip().lower()
    except (IndexError, ValueError) as exc:
        raise ValidationDomainError(code="invalid_file_payload", message="Invalid file payload") from exc

    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValidationDomainError(code="invalid_file_type", message="Unsupported file type")

    expected_extension = MIME_TO_EXTENSION[mime_type]

    try:
        decoded = base64.b64decode(encoded_data)
    except (binascii.Error, ValueError) as exc:
        raise ValidationDomainError(code="invalid_file_payload", message="Invalid file payload") from exc

    _validate_size(len(decoded))
    _validate_content_match(expected_extension, decoded[:1024])
    return DecodedBase64File(content=decoded, extension=expected_extension)
