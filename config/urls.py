from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class HelloHorld(APIView):
    def get(self, request):
        return Response(
            {
               "message":"Hello Wrold!"
                
            },
            status=status.HTTP_200_OK
        )


urlpatterns = [
    path('', HelloHorld.as_view(), name="hello-world"),
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("apps.auths.urls")),
    path("api/v1/profiles/", include("apps.profiles.urls")),
    path("api/v1/social_auth/", include("apps.social_auth.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/managements/", include("apps.managements.urls")),
    path("api/v1/sales_team/", include("apps.sales_team.urls")),
    path("api/v1/admin_dashboard/", include("apps.admin_dashboard.urls")),
    
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
