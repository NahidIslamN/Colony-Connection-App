from rest_framework import serializers

from apps.managements.models import Colony


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