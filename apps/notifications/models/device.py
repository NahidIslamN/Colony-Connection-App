"""Device and push notification models for OneSignal integration."""

from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class Device(models.Model):
    """Store device player_id for push notifications via OneSignal."""

    PLATFORM_CHOICES = (
        ("ios", "iOS"),
        ("android", "Android"),
        ("web", "Web"),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_device",
        help_text="Last login device for this user",
    )
    player_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="OneSignal player ID from mobile/web SDK",
    )
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default="android",
        help_text="Device operating system",
    )
    device_token = models.CharField(
        max_length=500,
        blank=True,
        help_text="FCM token or APNS token for backup",
    )
    device_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Device model or name (optional, for tracking)",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether device is eligible for push notifications",
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        help_text="Last time device registered or refreshed",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Device"
        verbose_name_plural = "Devices"
        ordering = ["-last_activity"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                name="unique_active_device_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.platform} ({self.player_id[:20]}...)"
