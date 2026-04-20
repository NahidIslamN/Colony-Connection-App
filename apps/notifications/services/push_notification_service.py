"""OneSignal push notification service layer."""

import logging
from typing import Optional

import requests
from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from apps.notifications.models import Device

logger = logging.getLogger(__name__)


class OneSignalClient:
    """OneSignal API client for sending push notifications."""

    BASE_URL = "https://onesignal.com/api/v1"

    def __init__(self):
        self.app_id = settings.ONESIGNAL_APP_ID
        self.api_key = settings.ONESIGNAL_API_KEY
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json; charset=utf-8",
        }

    def send_notification(
        self,
        player_id: str,
        title: str,
        content: str,
        data: Optional[dict] = None,
    ) -> bool:
        """
        Send push notification to a single device via OneSignal.
        
        Args:
            player_id: OneSignal player ID
            title: Notification title
            content: Notification body
            data: Additional data payload (optional)
            
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "app_id": self.app_id,
            "include_player_ids": [player_id],
            "headings": {"en": title},
            "contents": {"en": content},
        }

        if data:
            payload["data"] = data

        try:
            response = requests.post(
                f"{self.BASE_URL}/notifications",
                json=payload,
                headers=self.headers,
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Push notification sent to {player_id}")
            return True
        except requests.RequestException as exc:
            logger.error(
                f"Failed to send push notification to {player_id}: {exc}",
                exc_info=True,
            )
            return False


@transaction.atomic
def register_device_player_id(
    user,
    player_id: str,
    platform: str,
    device_token: Optional[str] = None,
    device_name: Optional[str] = None,
) -> Device:
    """
    Register or update device player_id for a user (OneToOne: last login device).
    
    Uses select_for_update for row-level locking to ensure ACID compliance.
    
    Args:
        user: User instance
        player_id: OneSignal player ID
        platform: Device platform (ios/android/web)
        device_token: Optional backup token (FCM/APNS)
        device_name: Optional device model/name
        
    Returns:
        Device instance (created or updated)
        
    Raises:
        serializers.ValidationError: If player_id is already assigned to another user
    """
    existing_device = Device.objects.filter(player_id=player_id).select_for_update().first()

    if existing_device and existing_device.user_id != user.id:
        raise serializers.ValidationError(
            {"player_id": "This device is already registered to another user."}
        )

    device, created = Device.objects.select_for_update().update_or_create(
        user=user,
        defaults={
            "player_id": player_id,
            "platform": platform,
            "device_token": device_token or "",
            "device_name": device_name or "",
            "is_active": True,
        },
    )

    logger.info(
        f"Device {'created' if created else 'updated'} for user {user.email}: {player_id}"
    )
    return device


def get_user_device(user) -> Optional[Device]:
    """Get the last login device for a user."""
    return Device.objects.filter(user=user, is_active=True).first()


def send_push_notification_to_user(
    user,
    title: str,
    content: str,
    data: Optional[dict] = None,
) -> bool:
    """
    Send push notification to user's last login device.
    
    Args:
        user: User instance
        title: Notification title
        content: Notification body
        data: Additional data payload (optional)
        
    Returns:
        True if sent successfully, False otherwise
    """
    device = get_user_device(user)
    if not device or not device.is_active:
        logger.warning(f"No active device found for user {user.email}")
        return False

    client = OneSignalClient()
    return client.send_notification(device.player_id, title, content, data)


def deactivate_device(player_id: str) -> bool:
    """Mark a device as inactive (user logged out from it)."""
    try:
        device = Device.objects.get(player_id=player_id)
        device.is_active = False
        device.save(update_fields=["is_active"])
        logger.info(f"Device {player_id} deactivated")
        return True
    except Device.DoesNotExist:
        logger.warning(f"Device {player_id} not found")
        return False
