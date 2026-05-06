from django.urls import path

from apps.admin_dashboard.views.company_managements import (
	CompanyForAssignmentAPIView,
	CompanyManagementAdminView,
	SupportMessageAdminView,
	DataAnalyticsAdminView,
)
from apps.admin_dashboard.views.termscondition import TermsConditionAdminView, TermsConditionPublicView,AboutUs

urlpatterns = [
    path("data-analytics/", DataAnalyticsAdminView.as_view(), name="admin-dashboard-company-list-create"),
    
	path("companies/", CompanyManagementAdminView.as_view(), name="admin-dashboard-company-list-create"),
	path("companies/<int:pk>/", CompanyManagementAdminView.as_view(), name="admin-dashboard-company-detail"),
	path("company/company-for-assignment/", CompanyForAssignmentAPIView.as_view(), name="company-for-assignment"),
	path("supports/", SupportMessageAdminView.as_view(), name="admin-dashboard-support-messages"),
	path("terms-conditions/public/", TermsConditionPublicView.as_view(), name="terms-conditions-public-list"),
	path("terms-conditions/", TermsConditionAdminView.as_view(), name="terms-conditions-admin-list-create"),
    path("about-us/", AboutUs.as_view(), name="terms-conditions-admin-list-create"),
	path("terms-conditions/<int:pk>/", TermsConditionAdminView.as_view(), name="terms-conditions-admin-detail"),
    
]
