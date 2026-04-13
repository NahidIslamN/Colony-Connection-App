from django.contrib import admin

from apps.auths.models import CustomUser, OtpTable

admin.site.register(CustomUser)
admin.site.register(OtpTable)
