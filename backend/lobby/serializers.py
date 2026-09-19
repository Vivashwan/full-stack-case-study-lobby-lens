from rest_framework import serializers

from .models import Casino, Geography


class GeographySerializer(serializers.ModelSerializer):
    class Meta:
        model = Geography
        fields = ["id", "name", "country_code"]


class CasinoSerializer(serializers.ModelSerializer):
    # operator/geography come from select_related() on the queryset (no extra query);
    # approved_runs comes from an annotate(approved_runs_count=...) on the queryset
    # instead of a per-row .count() query - see CasinoList.get_queryset (task C3).
    operator_name = serializers.CharField(source="operator.name")
    geography_name = serializers.CharField(source="geography.name")
    approved_runs = serializers.IntegerField(source="approved_runs_count")

    class Meta:
        model = Casino
        fields = ["id", "name", "operator_name", "geography_name", "is_active", "approved_runs"]
