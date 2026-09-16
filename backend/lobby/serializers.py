from rest_framework import serializers

from .models import Casino, Geography


class GeographySerializer(serializers.ModelSerializer):
    class Meta:
        model = Geography
        fields = ["id", "name", "country_code"]


class CasinoSerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source="operator.name")
    geography_name = serializers.CharField(source="geography.name")
    approved_runs = serializers.SerializerMethodField()

    class Meta:
        model = Casino
        fields = ["id", "name", "operator_name", "geography_name", "is_active", "approved_runs"]

    def get_approved_runs(self, obj):
        return obj.runs.filter(show_data=True).count()
