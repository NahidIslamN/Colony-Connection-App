from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL



class Company(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=250)
    ceo_name = models.CharField(max_length=250)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    plan = models.ForeignKey("SubscribePlan", on_delete=models.SET_NULL, null=True, blank=True)
    subscription_package = models.ForeignKey("SubscribePlan", on_delete=models.SET_NULL, null=True, blank=True)
    is_subscribe = models.BooleanField(default=False)
    expire_date = models.DateField()

    def __str__(self):
        return self.company_name
    

class SalesRepresentative(models.Model):
    STATUS_CHOICES = (
        ('active', "Active"),
        ('inactive', "Inactive"),
        ('on_leave', 'On Leave'),
    )
    company = models.ForeignKey("Company", on_delete=models.CASCADE)
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    full_name = models.CharField(max_length=250)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')

    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.full_name


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    owner_name = models.CharField(max_length=250)
    company_name = models.CharField(max_length=250)
    industry = models.CharField(max_length=100)
    company_type = models.CharField(max_length=100)

    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)

    street_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    location_url = models.URLField(verbose_name='colony_location', null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    sales_reps = models.ManyToManyField(
        "SalesRepresentative",
        related_name='customers'
    )

    def __str__(self):
        return self.company_name
    

class Colony(models.Model):
    colony_owner = models.ForeignKey("Company", on_delete=models.CASCADE)

    name = models.CharField(max_length=250, db_index=True)
    region = models.CharField(max_length=250, db_index=True)

    sales_reps = models.ManyToManyField(
        "SalesRepresentative",
        related_name='colonies'
    )

    customers = models.ManyToManyField(
        "Customer",
        related_name='colonies'
    )

    location_url = models.URLField(verbose_name='colony_location')

    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('name', 'region')
    

class VisitColony(models.Model):
    colony = models.ForeignKey("Colony", on_delete=models.CASCADE)
    date = models.DateField()

    # Customers assigned to this colony but not yet visited
    pending_customers = models.ManyToManyField(
        'Customer', 
        related_name='pending_colonies',
        blank=True
    )
    # Customers who have successfully been visited
    completed_customers = models.ManyToManyField(
        'Customer', 
        related_name='completed_colonies',
        blank=True
    )
    is_visited = models.BooleanField(default=True)


class CustomerNote(models.Model):
    date = models.DateField()
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class CustomerMechanary(models.Model):
    date = models.DateField()
    customer = models.ForeignKey("Customer", on_delete=models.CASCADE)
    type = models.CharField(max_length=250)
    brand = models.CharField(max_length=250)
    model = models.CharField(max_length=250)
    serial_number = models.CharField(max_length=250)
    purchase_year = models.DateField()
    condition = models.CharField(max_length=250)
    next_nervice = models.CharField(max_length=250)
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)