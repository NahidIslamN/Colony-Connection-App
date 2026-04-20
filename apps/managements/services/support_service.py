from django.db import transaction

from apps.managements.models import SupportFile, SupportModel


def create_support_message(validated_data: dict) -> SupportModel:
    files = validated_data.pop("files", [])

    with transaction.atomic():
        support_message = SupportModel.objects.create(**validated_data)

        if files:
            support_files = [SupportFile.objects.create(file=file_obj) for file_obj in files]
            support_message.files.set(support_files)

    return support_message
