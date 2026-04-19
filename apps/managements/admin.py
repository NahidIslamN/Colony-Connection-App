from django.contrib import admin

from .models import (
    Colony,
    Company,
    Customer,
    CustomerMechanary,
    CustomerNote,
    SalesRepresentative,
    SubscribePlan,
    VisitColony,
)


@admin.register(SubscribePlan)
class SubscribePlanAdmin(admin.ModelAdmin):
    list_display = (
        "plan_Name",
        "price_monthly",
        "price_yearly",
        "user_limit",
        "colony_limit",
        "is_unlimit_users",
        "is_unlimit_colony",
    )
    search_fields = ("plan_Name",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "ceo_name",
        "email",
        "phone",
        "subscription_package",
        "is_subscribe",
        "expire_date",
    )
    search_fields = ("company_name", "ceo_name", "email", "phone")
    list_filter = ("is_subscribe", "subscription_package", "expire_date")
    autocomplete_fields = ("user", "subscription_package")


@admin.register(SalesRepresentative)
class SalesRepresentativeAdmin(admin.ModelAdmin):
    list_display = ("full_name", "company", "status", "email", "phone")
    search_fields = ("full_name", "email", "phone", "company__company_name")
    list_filter = ("status", "company")
    autocomplete_fields = ("company", "user")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "owner_name",
        "industry",
        "company_type",
        "email",
        "phone",
        "city",
        "country",
    )
    search_fields = (
        "company_name",
        "owner_name",
        "email",
        "phone",
        "industry",
        "city",
        "country",
    )
    list_filter = ("industry", "company_type", "city", "country")
    autocomplete_fields = ("user", "sales_reps")


@admin.register(Colony)
class ColonyAdmin(admin.ModelAdmin):
    list_display = ("name", "region", "colony_owner", "latitude", "longitude")
    search_fields = ("name", "region", "colony_owner__company_name")
    list_filter = ("region", "colony_owner")
    autocomplete_fields = ("colony_owner", "sales_reps", "customers")


@admin.register(VisitColony)
class VisitColonyAdmin(admin.ModelAdmin):
    list_display = ("colony", "date", "is_visited")
    search_fields = ("colony__name",)
    list_filter = ("is_visited", "date")
    autocomplete_fields = ("colony", "pending_customers", "completed_customers")


@admin.register(CustomerNote)
class CustomerNoteAdmin(admin.ModelAdmin):
    list_display = ("customer", "date", "created_at")
    search_fields = ("customer__company_name", "note")
    list_filter = ("date", "created_at")
    autocomplete_fields = ("customer",)


@admin.register(CustomerMechanary)
class CustomerMechanaryAdmin(admin.ModelAdmin):
    list_display = ("customer", "type", "brand", "model", "serial_number", "purchase_year")
    search_fields = ("customer__company_name", "type", "brand", "model", "serial_number")
    list_filter = ("type", "brand", "purchase_year")
    autocomplete_fields = ("customer",)