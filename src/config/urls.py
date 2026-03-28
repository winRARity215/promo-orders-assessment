from django.contrib import admin
from django.urls import path

from orders.api.views import create_order_api


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/orders/", create_order_api),
]
