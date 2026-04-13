from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone


@shared_task
def update_last_activity(user_id):
    user_model = get_user_model()
    updated = user_model.objects.filter(id=user_id).update(last_activity=timezone.now())
    if updated:
        return "last_activity timestamp updated."
    return "User not found."
