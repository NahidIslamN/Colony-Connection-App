from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class NoteModel(models.Model):
    NOTE_TYPE = (
        ("success", "Success"),
        ("warning", "Warning"),
        ("normal", "Normal"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    note_type = models.CharField(max_length=25, choices=NOTE_TYPE, default="normal")
    is_seen = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        # Keep using the existing table created by chats migrations.
        db_table = "chats_notemodel"

    def __str__(self):
        return self.title
