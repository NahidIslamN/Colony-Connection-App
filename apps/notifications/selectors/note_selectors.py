from apps.notifications.models import NoteModel


def get_unseen_notifications_count_for_user(user) -> int:
    return NoteModel.objects.filter(user=user, is_seen=False).count()


def get_notifications_for_user(user):
    return NoteModel.objects.filter(user=user)


def mark_unseen_notifications_as_seen(user):
    return NoteModel.objects.filter(user=user, is_seen=False).update(is_seen=True)
