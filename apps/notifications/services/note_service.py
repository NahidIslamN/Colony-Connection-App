from apps.notifications.selectors.note_selectors import (
    get_notifications_for_user,
    get_unseen_notifications_count_for_user,
    mark_unseen_notifications_as_seen,
)


def get_unseen_notifications_count(user) -> int:
    return get_unseen_notifications_count_for_user(user)


def get_notifications_and_mark_seen(user):
    notifications = get_notifications_for_user(user)
    mark_unseen_notifications_as_seen(user)
    return notifications
