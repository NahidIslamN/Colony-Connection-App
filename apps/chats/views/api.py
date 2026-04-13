import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.chats.serializers.input import ChatOrGroupCreateInputSerializer, SendMessageInputSerializer
from apps.chats.serializers.output import (
    ChatCreateOutputSerializer,
    ChatListOutputSerializer,
    MessageListOutputSerializer,
)
from apps.chats.services.chat_service import (
    ChatServiceError,
    create_chat_or_group,
    ensure_user_in_chat,
    get_chat_or_raise,
    hydrate_last_messages,
    list_user_chats,
)
from apps.chats.services.message_service import MessageServiceError, list_messages, notify_message_sent, send_message
from core.exceptions import ValidationDomainError
from core.pagination import CustomPagination
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)


class ChatCreateListView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        chats = list_user_chats(request.user)
        paginator = CustomPagination()
        paginator.page_size = 250
        paginator.page_size_query_param = None
        page = paginator.paginate_queryset(chats, request)
        page = hydrate_last_messages(page)
        serializer = ChatListOutputSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = ChatOrGroupCreateInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("validation errors!", status.HTTP_400_BAD_REQUEST, errors=serializer.errors)

        user_list = serializer.validated_data.get("user_list", [])
        group_name = serializer.validated_data.get("group_name", "")

        try:
            chat, already_exists = create_chat_or_group(request.user, user_list, group_name)
        except ChatServiceError:
            return error_response(
                "validation errors!",
                status.HTTP_400_BAD_REQUEST,
                errors={"message": "invalid python list! plece semt an arry to add user"},
            )

        output = ChatCreateOutputSerializer(chat, context={"request": request}).data
        if already_exists:
            return success_response("already exiest chat!", status.HTTP_200_OK, data=output)

        return success_response("successfully created!", status.HTTP_201_CREATED, data=output)


class MessageListChatsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request, inbox_id):
        try:
            chat = get_chat_or_raise(inbox_id)
            ensure_user_in_chat(chat, request.user)
        except ChatServiceError as exc:
            if str(exc) == "chat_not_found":
                return error_response("inbox not found!", status.HTTP_404_NOT_FOUND)
            return error_response("You are not a member of this chat!", status.HTTP_400_BAD_REQUEST)

        messages = list_messages(chat, request.user)
        paginator = CustomPagination()
        page = paginator.paginate_queryset(messages, request)
        serializer = MessageListOutputSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class SentMessageChatsView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def post(self, request, inbox_id):
        try:
            chat = get_chat_or_raise(inbox_id)
        except ChatServiceError:
            return error_response("chat not found!", status.HTTP_404_NOT_FOUND)

        try:
            ensure_user_in_chat(chat, request.user)
        except ChatServiceError:
            return error_response("you are not a member of this chat!", status.HTTP_403_FORBIDDEN)

        serializer = SendMessageInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("validation errors!", status.HTTP_400_BAD_REQUEST, errors=serializer.errors)

        files = request.FILES.getlist("files") if "files" in request.FILES else []

        try:
            message = send_message(chat=chat, sender=request.user, message_text=serializer.validated_data.get("message", ""), files=files)
        except MessageServiceError:
            return error_response("message must contain either text or files", status.HTTP_400_BAD_REQUEST)
        except ValidationDomainError as exc:
            return error_response(exc.message, status.HTTP_400_BAD_REQUEST, errors={"code": exc.code})
        except (OSError, ValueError, TypeError) as exc:
            logger.exception("Unexpected error while sending message", extra={"chat_id": inbox_id, "user_id": request.user.id})
            return error_response(
                "error sending message",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                errors={"code": "message_send_failed"},
            )

        output = MessageListOutputSerializer(message).data
        notify_message_sent(chat.id, output)
        return success_response("message sent successfully!", status.HTTP_201_CREATED, data=output)
