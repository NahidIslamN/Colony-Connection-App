import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView

from apps.managements.models import Company, Colony,SubscribePlan

from core.custom_permission import IsSalesRep
from core.pagination import CustomPagination
from core.responses import error_response, success_response

logger = logging.getLogger(__name__)

# write your views here



