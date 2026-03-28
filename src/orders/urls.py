from __future__ import annotations

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .api.views import OrderCreateAPIView, OrderViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")

app_name = "orders"

urlpatterns = [
    path("create/", OrderCreateAPIView.as_view(), name="order_create"),
    path("api/v1/", include(router.urls)),
]
