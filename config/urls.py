from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.auths.urls")),
    path("api/v1/profiles/", include("apps.profiles.urls")),
    path("api/v1/social_auth/", include("apps.social_auth.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/managements/", include("apps.managements.urls")),
    path("api/v1/sales_team/", include("apps.sales_team.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
