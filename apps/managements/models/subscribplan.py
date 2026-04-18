from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class SubscribePlan(models.Model):
    plan_Name = models.CharField(max_length=250)
    price_monthly = models.DecimalField(max_digits=9, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=9, decimal_places=2)
    user_limit = models.IntegerField()
    colony_limit = models.IntegerField()
    is_unlimit_users = models.BooleanField(default=False)
    is_unlimit_colony = models.BooleanField(default=False)
