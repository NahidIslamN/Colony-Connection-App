from rest_framework import serializers


class VisitColonyReportQueryInputSerializer(serializers.Serializer):
	date = serializers.DateField(required=True, input_formats=["%Y-%m-%d"])

