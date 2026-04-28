from django.db import models


class SubscribePlan(models.Model):
    plan_Name = models.CharField(max_length=250)
    price_monthly = models.DecimalField(max_digits=9, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=9, decimal_places=2)
    user_limit = models.IntegerField()
    colony_limit = models.IntegerField()
    is_unlimit_users = models.BooleanField(default=False)
    is_unlimit_colony = models.BooleanField(default=False)



class Invoice(models.Model):
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    plan = models.ForeignKey("SubscribePlan", on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    payment_ammount = models.DecimalField(max_digits=9, decimal_places=2)



