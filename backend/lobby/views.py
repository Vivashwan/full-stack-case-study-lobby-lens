from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import services
from .models import Casino, Geography
from .serializers import CasinoSerializer, GeographySerializer


class GeographyList(generics.ListAPIView):
    """GET /api/geographies/"""

    queryset = Geography.objects.all()
    serializer_class = GeographySerializer
    pagination_class = None


class CasinoList(generics.ListAPIView):
    """GET /api/casinos/?geography=<id>&is_active=true|false  (paginated, 20 per page)"""

    serializer_class = CasinoSerializer

    def get_queryset(self):
        qs = Casino.objects.all().order_by("name")
        geo = self.request.query_params.get("geography")
        if geo:
            qs = qs.filter(geography_id=geo)
        active = self.request.query_params.get("is_active")
        if active in ("true", "false"):
            qs = qs.filter(is_active=(active == "true"))
        return qs


@api_view(["GET"])
def summary(request):
    """GET /api/summary/?month=YYYY-MM[&geography=<id>]"""
    month = request.query_params.get("month")
    if not month:
        return Response({"detail": "month is required"}, status=status.HTTP_400_BAD_REQUEST)
    geo = request.query_params.get("geography")
    try:
        data = services.run_summary(month, int(geo) if geo else None)
    except (services.InvalidMonth, ValueError) as e:
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(data)


@api_view(["GET"])
def provider_market_share(request):
    """
    GET /api/provider-market-share/?geography=<id>&month=YYYY-MM

    TODO (task C2): validate the query params, call services.provider_market_share
    and return the response described in CASE_STUDY.md -> "API contract".
    """
    return Response({"detail": "not implemented yet"}, status=status.HTTP_501_NOT_IMPLEMENTED)
