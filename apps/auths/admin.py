from django.contrib import admin

from apps.auths.models import CustomUser, OtpTable


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
	list_display = ("id", "email", "full_name", "phone", "role", "status", "is_active")
	search_fields = ("email", "full_name", "phone")
	list_filter = ("role", "status", "is_active", "is_staff", "is_superuser")


@admin.register(OtpTable)
class OtpTableAdmin(admin.ModelAdmin):
	search_fields = ("email",)
