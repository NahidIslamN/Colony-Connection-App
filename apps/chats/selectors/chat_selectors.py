from django.contrib.auth import get_user_model
from django.db.models import Prefetch, Q, Subquery, OuterRef

from apps.chats.models import Chat, Message

User = get_user_model()


def get_user_chats(user):
    last_message_qs = Message.objects.filter(chat=OuterRef("pk")).order_by("-created_at")
    participant_qs = User.objects.only("id", "full_name", "image", "last_activity")

    return (
        Chat.objects.filter(participants=user)
        .prefetch_related(Prefetch("participants", queryset=participant_qs, to_attr="prefetched_participants"))
        .annotate(
            last_message_id=Subquery(last_message_qs.values("id")[:1]),
            last_message_text=Subquery(last_message_qs.values("text")[:1]),
            last_message_status=Subquery(last_message_qs.values("status")[:1]),
            last_message_sender_name=Subquery(last_message_qs.values("sender__full_name")[:1]),
            last_message_created_at=Subquery(last_message_qs.values("created_at")[:1]),
            last_message_updated_at=Subquery(last_message_qs.values("updated_at")[:1]),
        )
        .order_by("-updated_at")
    )


def get_chat_by_id(chat_id: int):
    return Chat.objects.prefetch_related("participants").filter(id=chat_id).first()


def find_private_chat_between_users(user_a, user_b):
    return Chat.objects.filter(
        Q(inviter=user_a, invitee=user_b) | Q(inviter=user_b, invitee=user_a),
        chat_type="private",
    ).first()


def get_user_by_id(user_id: int):
    return User.objects.get(id=user_id)


def get_chat_participant_ids(chat_id: int) -> list[int]:
    return list(
        Chat.objects.filter(id=chat_id).values_list("participants__id", flat=True)
    )
