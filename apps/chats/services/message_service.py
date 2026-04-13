from django.db import transaction

from apps.chats.models import Message, MessageFiles
from apps.chats.selectors.message_selectors import get_chat_messages, mark_non_sender_messages_as_seen
from apps.chats.tasks.message_tasks import sent_message_to_chat
from common.file_validation import validate_file_batch, validate_uploaded_file
from infrastructure.security_scan import enqueue_file_scan


class MessageServiceError(Exception):
    pass


def list_messages(chat, user):
    mark_non_sender_messages_as_seen(chat, user)
    return get_chat_messages(chat)


def send_message(chat, sender, message_text, files):
    text = (message_text or "").strip()
    if not text and not files:
        raise MessageServiceError("empty_message")

    validate_file_batch(len(files))

    with transaction.atomic():
        message = Message.objects.create(chat=chat, sender=sender, text=text or None)
        for file_obj in files:
            validate_uploaded_file(file_obj)
            msg_file = MessageFiles.objects.create(title=file_obj.name, file=file_obj)
            message.files.add(msg_file)
            enqueue_file_scan(msg_file.file.name, {"chat_id": chat.id, "sender_id": sender.id})

        chat.save()
        return message


def notify_message_sent(chat_id: int, payload: dict):
    sent_message_to_chat.delay(chat_id, payload)
