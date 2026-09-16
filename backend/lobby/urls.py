from django.urls import path

from . import views

urlpatterns = [
    path("geographies/", views.GeographyList.as_view()),
    path("casinos/", views.CasinoList.as_view()),
    path("summary/", views.summary),
    path("provider-market-share/", views.provider_market_share),
]
