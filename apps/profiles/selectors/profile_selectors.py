from apps.profiles.models import UserProfile


def get_or_create_profile_for_user(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile
