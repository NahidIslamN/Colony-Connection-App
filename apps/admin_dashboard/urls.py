from django.urls import path

from apps.admin_dashboard.views.company_managements import CompanyManagementAdminView, SupportMessageAdminView

urlpatterns = [
	path("companies/", CompanyManagementAdminView.as_view(), name="admin-dashboard-company-list-create"),
	path("companies/<int:pk>/", CompanyManagementAdminView.as_view(), name="admin-dashboard-company-detail"),
	path("supports/", SupportMessageAdminView.as_view(), name="admin-dashboard-support-messages"),
]
