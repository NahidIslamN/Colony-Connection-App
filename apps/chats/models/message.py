from django.conf import settings
from django.db import models

from apps.chats.models.chat import Chat

User = settings.AUTH_USER_MODEL


class MessageReaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reactions")
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)


class Call(models.Model):
    CALL_TYPE_CHOICES = (("audio", "Audio"), ("video", "Video"))

    call_type = models.CharField(max_length=10, choices=CALL_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.call_type} call {self.id}"


class MessageFiles(models.Model):
    title = models.CharField(max_length=30, null=True, blank=True)
    file = models.FileField(upload_to="messages_files", blank=True)


class Message(models.Model):
    STATUS_CHOICES = (("sent", "Sent"), ("delivered", "Delivered"), ("seen", "Seen"))

    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    text = models.TextField(blank=True, null=True)
    files = models.ManyToManyField(MessageFiles, blank=True, related_name="files")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="sent")
    reactions = models.ManyToManyField(MessageReaction, related_name="message_reactions")
    seen_users = models.ManyToManyField(User, related_name="seen_users", blank=True)
    calls = models.ForeignKey(Call, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} -> Chat {self.chat.id}"
