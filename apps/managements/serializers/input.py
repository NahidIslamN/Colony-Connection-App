from rest_framework import serializers
from django.contrib.auth import get_user_model

from apps.managements.models import Colony, SalesRepresentative

User = get_user_model()


class ColonyInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colony
        fields = ('name', 'region', 'sales_reps', 'customers', 'location_url', 'latitude', 'longitude')


class ColonyCreateUpdateInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colony
        fields = ('name', 'region', 'sales_reps', 'customers', 'location_url', 'latitude', 'longitude')


class ColonyPatchInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colony
        fields = ('name', 'region', 'sales_reps', 'customers', 'location_url', 'latitude', 'longitude')
        extra_kwargs = {
            'name': {'required': False},
            'region': {'required': False},
            'sales_reps': {'required': False},
            'customers': {'required': False},
            'location_url': {'required': False},
            'latitude': {'required': False},
            'longitude': {'required': False},
        }



# Sales Representative Management


class SalesRepresentativeCreateUpdateInputSerializer(serializers.Serializer):
    """
    Serializer to create a SalesRepresentative with a new User and assign colonies.
    
    Steps:
    1. Create User with email, full_name, phone, password
    2. Create SalesRepresentative with that user
    3. Assign colonies to the SalesRepresentative
    """
    # User creation fields
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(max_length=250, required=True)
    phone = serializers.CharField(max_length=20, required=True)
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    
    # Sales Rep fields
    status = serializers.ChoiceField(choices=['active', 'inactive', 'on_leave'], default='inactive')
    
    # Colony assignment
    colony_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="List of colony IDs to assign to this sales representative"
    )
    
    def validate_email(self, value):
        """Check if email already exists."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_phone(self, value):
        """Check if phone already exists."""
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone already exists.")
        return value


class SalesRepresentativeUpdateInputSerializer(serializers.ModelSerializer):
    """Serializer to update an existing SalesRepresentative."""
    class Meta:
        model = SalesRepresentative
        fields = ("full_name", "status", "email", "phone")
        extra_kwargs = {
            "full_name": {"required": True},
            "status": {"required": True},
            "email": {"required": True},
            "phone": {"required": True},
        }


class SalesRepresentativePatchInputSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = SalesRepresentative
        fields = ("user", "full_name", "status", "email", "phone")
        extra_kwargs = {
            "full_name": {"required": False},
            "status": {"required": False},
            "email": {"required": False},
            "phone": {"required": False},
        }


class AssignSalesRepToColoniesInputSerializer(serializers.Serializer):
    """Serializer for assigning a sales rep to multiple colonies."""
    colony_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text="List of colony IDs to assign to this sales representative"
    )
    
    def validate_colony_ids(self, value):
        if not value:
            raise serializers.ValidationError("Colony IDs list cannot be empty")
        return value


class GetColoniesForSalesRepOutputSerializer(serializers.Serializer):
    """Serializer to list colonies assigned to a sales rep."""
    colony_id = serializers.IntegerField(source='id')
    colony_name = serializers.CharField(source='name')
    region = serializers.CharField()
    status = serializers.CharField()
    sales_reps_count = serializers.SerializerMethodField()
    
    def get_sales_reps_count(self, obj):
        return obj.sales_reps.count()
