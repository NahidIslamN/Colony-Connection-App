from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Chat(models.Model):
    CHAT_TYPE_CHOICES = (("private", "Private"), ("group", "Group"))

    chat_type = models.CharField(max_length=10, choices=CHAT_TYPE_CHOICES, default="private")
    participants = models.ManyToManyField(User, related_name="chats")
    name = models.CharField(max_length=255, blank=True, null=True)
    inviter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_invites", null=True, blank=True)
    invitee = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_invites", null=True, blank=True)
    is_accepted_invitee = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.name or f"{self.chat_type} Chat {self.id}"


class BlockList(models.Model):
    blocker = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_users")
    blocked = models.ForeignKey(User, on_delete=models.CASCADE, related_name="blocked_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("blocker", "blocked")
