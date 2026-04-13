from django.db import transaction

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from apps.chats.models import Chat, Message, MessageFiles
from apps.chats.selectors.chat_selectors import (
    find_private_chat_between_users,
    get_chat_participant_ids,
    get_chat_by_id,
    get_user_by_id,
    get_user_chats,
)
from apps.notifications.tasks.notification_tasks import sent_note_to_user
from common.file_validation import decode_and_validate_base64_file, validate_file_batch
from core.exceptions import NotFoundDomainError, PermissionDomainError, ValidationDomainError
from infrastructure.security_scan import enqueue_file_scan

User = get_user_model()


class ChatServiceError(Exception):
    pass


def list_user_chats(user):
    return get_user_chats(user)


def hydrate_last_messages(chats):
    message_ids = [chat.last_message_id for chat in chats if getattr(chat, "last_message_id", None)]
    if not message_ids:
        return chats

    messages = (
        Message.objects.filter(id__in=message_ids)
        .select_related("sender")
        .prefetch_related("files")
    )
    message_map = {message.id: message for message in messages}
    for chat in chats:
        chat.prefetched_last_message = message_map.get(getattr(chat, "last_message_id", None))
    return chats


def create_chat_or_group(current_user, user_list, group_name):
    participants = list(dict.fromkeys(list(user_list) + [current_user.id]))
    participant_users = _resolve_users_or_raise(participants)

    with transaction.atomic():
        if len(participants) == 2:
            invitee = next(user for user in participant_users if user.id != current_user.id)
            existing_chat = find_private_chat_between_users(current_user, invitee)
            if existing_chat:
                return existing_chat, True

            chat = Chat.objects.create(
                chat_type="private",
                name=group_name,
                inviter=current_user,
                invitee=invitee,
            )
            _attach_participants(chat, participant_users)
            return chat, False

        chat = Chat.objects.create(
            chat_type="group",
            name=group_name,
            inviter=current_user,
            is_accepted_invitee=True,
        )
        _attach_participants(chat, participant_users)

    for user in participant_users:
        if user.id != current_user.id:
            sent_note_to_user.delay(
                user_id=user.id,
                title="Added to Group",
                content=f"You've been added to group '{chat.name}' by {current_user.first_name} {current_user.last_name}",
                note_type="normal",
            )

    return chat, False


def get_chat_or_raise(chat_id: int):
    chat = get_chat_by_id(chat_id)
    if not chat:
        raise ChatServiceError("chat_not_found")
    return chat


def ensure_user_in_chat(chat, user):
    if user not in chat.participants.all():
        raise ChatServiceError("chat_forbidden")


def _resolve_users_or_raise(participant_ids):
    users = []
    for user_id in participant_ids:
        try:
            users.append(get_user_by_id(user_id))
        except User.DoesNotExist as exc:
            raise ChatServiceError("invalid_user_list") from exc
    return users


def _attach_participants(chat, participant_users):
    for user in participant_users:
        chat.participants.add(user)


def create_chat_message(user, chat_id: int, message_text: str, files: list):
    chat = get_chat_by_id(chat_id)
    if chat is None:
        raise NotFoundDomainError(code="chat_not_found", message="Chat not found")

    if not chat.participants.filter(id=user.id).exists():
        raise PermissionDomainError(code="chat_forbidden", message="You are not a member of this chat")

    validate_file_batch(len(files))

    with transaction.atomic():
        message_obj = Message.objects.create(chat=chat, sender=user, text=message_text or None)

        for file_payload in files:
            title = file_payload.get("title", "")
            file_base64 = file_payload.get("file_base64")
            if not file_base64:
                continue

            try:
                decoded_file = decode_and_validate_base64_file(file_base64)
            except ValidationDomainError:
                raise

            message_file = MessageFiles.objects.create(
                title=title,
                file=ContentFile(
                    decoded_file.content,
                    name=f"{title or 'file'}.{decoded_file.extension}",
                ),
            )
            message_obj.files.add(message_file)
            enqueue_file_scan(
                message_file.file.name,
                {"chat_id": chat.id, "sender_id": user.id},
            )

        chat.save(update_fields=["updated_at"])
        return message_obj


def list_chat_participant_ids(chat_id: int) -> list[int]:
    return [user_id for user_id in get_chat_participant_ids(chat_id) if user_id is not None]
