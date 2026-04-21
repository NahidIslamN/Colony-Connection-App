from django.urls import path

from apps.admin_dashboard.views.company_managements import CompanyManagementAdminView, SupportMessageAdminView
from apps.admin_dashboard.views.termscondition import TermsConditionAdminView, TermsConditionPublicView

urlpatterns = [
	path("companies/", CompanyManagementAdminView.as_view(), name="admin-dashboard-company-list-create"),
	path("companies/<int:pk>/", CompanyManagementAdminView.as_view(), name="admin-dashboard-company-detail"),
	path("supports/", SupportMessageAdminView.as_view(), name="admin-dashboard-support-messages"),
	path("terms-conditions/public/", TermsConditionPublicView.as_view(), name="terms-conditions-public-list"),
	path("terms-conditions/public/<int:pk>/", TermsConditionPublicView.as_view(), name="terms-conditions-public-detail"),
	path("terms-conditions/", TermsConditionAdminView.as_view(), name="terms-conditions-admin-list-create"),
	path("terms-conditions/<int:pk>/", TermsConditionAdminView.as_view(), name="terms-conditions-admin-detail"),
]
