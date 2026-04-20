from django.contrib import admin
from apps.notifications.models import NoteModel
from .models import Device




@admin.register(NoteModel)
class NoteModelAdmin(admin.ModelAdmin):
    """Admin panel for user notes management."""

    search_fields = (
        "user__email",
        "user__username",
        "title",
        "content",
    )

  
    list_filter = (
        "note_type",
        "is_seen",
        "created_at",
        "updated_at",
    )

   
    list_display = (
        "title",
        "user",
        "note_type",
        "is_seen",
        "short_content",
        "created_at",
    )

    
    list_select_related = ("user",)
    ordering = ("-created_at",)

   
    readonly_fields = ("created_at", "updated_at")

   
    list_editable = ("is_seen",)
    list_per_page = 25

   
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    short_content.short_description = "Content Preview"



@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    """Advanced admin panel for Device model (OneSignal push tracking)."""

    search_fields = (
        "user__email",
        "user__username",
        "player_id",
        "device_token",
        "device_name",
    )

    list_filter = (
        "platform",
        "is_active",
        "created_at",
        "updated_at",
        "last_activity",
    )


    list_display = (
        "user",
        "platform",
        "short_player_id",
        "device_name",
        "is_active",
        "last_activity",
    )


    list_select_related = ("user",)
    ordering = ("-last_activity",)

    readonly_fields = (
        "created_at",
        "updated_at",
        "last_activity",
    )

    autocomplete_fields = ("user",)

    def short_player_id(self, obj):
        return f"{obj.player_id[:25]}..."
    short_player_id.short_description = "Player ID"