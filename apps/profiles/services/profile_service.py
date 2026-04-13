import os

from django.db import transaction

from apps.profiles.selectors.profile_selectors import get_or_create_profile_for_user
from common.file_validation import validate_uploaded_image


def update_my_account(user, data):
    profile_data = data.pop("profile", None)
    image = data.pop("image", None)

    user.email = data.get("email", user.email)
    user.full_name = data.get("full_name", user.full_name)
    user.phone = data.get("phone", user.phone)

    with transaction.atomic():
        if image:
            validate_uploaded_image(image)

            if user.image:
                try:
                    user.image.delete(save=False)
                except (FileNotFoundError, OSError, ValueError):
                    pass

            ext = os.path.splitext(image.name)[1]
            filename = f"profile/{user.id}{ext}"
            user.image.save(filename, image, save=False)

        user.save()

        if profile_data:
            profile = get_or_create_profile_for_user(user)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return user
