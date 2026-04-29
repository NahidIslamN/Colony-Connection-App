from django.db import models


class SubscriptionFeatures(models.Model):
    text = models.CharField(max_length=250)
    def __str__(self):
        return self.text

class SubscribePlan(models.Model):
    plan_Name = models.CharField(max_length=250)
    price_monthly = models.DecimalField(max_digits=9, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=9, decimal_places=2)
    user_limit = models.IntegerField()
    colony_limit = models.IntegerField()
    is_unlimit_users = models.BooleanField(default=False)
    is_unlimit_colony = models.BooleanField(default=False)
    features = models.ManyToManyField(SubscriptionFeatures, related_name="features", blank=True)



class Invoice(models.Model):
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    plan = models.ForeignKey("SubscribePlan", on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    payment_ammount = models.DecimalField(max_digits=9, decimal_places=2)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    stripe_subscription_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    currency = models.CharField(max_length=12, null=True, blank=True)
    paid = models.BooleanField(default=False)
    metadata = models.JSONField(null=True, blank=True)


class WebhookEvent(models.Model):
    """Idempotency log for processed Stripe webhook events."""
    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    payload = models.JSONField(null=True, blank=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.event_id



