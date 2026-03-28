from django.contrib import admin
from .models import PromoCode, Order, OrderItem, PromoCodeRedemption


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    
    list_display = [
        "code", 
        "discount_rate_display", 
        "category", 
        "max_usages", 
        "is_active", 
        "created_at"
    ]
    list_filter = [
        "is_active", 
        "category", 
        "created_at"
    ]
    search_fields = ["code"]
    
    def discount_rate_display(self, obj: PromoCode) -> str:
        return f"{obj.discount_rate * 100:.1f}%"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    
    list_display = [
        "id", 
        "user", 
        "promo_code", 
        "price", 
        "total", 
        "created_at"
    ]
    list_filter = [
        "created_at", 
        "promo_code"
    ]
    search_fields = ["id", "user__username"]
    readonly_fields = ["price", "total", "created_at"]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    
    list_display = [
        "order", 
        "good", 
        "quantity", 
        "unit_price", 
        "discount_rate_display", 
        "total"
    ]
    list_filter = [
        "order__created_at", 
        "good__category"
    ]
    search_fields = [
        "order__id", 
        "good__name"
    ]
    readonly_fields = ["unit_price", "total"]
    
    def discount_rate_display(self, obj: OrderItem) -> str:
        return f"{obj.discount_rate * 100:.1f}%"


@admin.register(PromoCodeRedemption)
class PromoCodeRedemptionAdmin(admin.ModelAdmin):
    
    list_display = [
        "promo_code", 
        "user", 
        "order", 
        "redeemed_at"
    ]
    list_filter = [
        "redeemed_at", 
        "promo_code"
    ]
    search_fields = [
        "user__username", 
        "promo_code__code"
    ]
    readonly_fields = ["redeemed_at"]
    
    def order_link(self, obj: PromoCodeRedemption) -> str:
        from django.urls import reverse
        from django.utils.safestring import mark_safe
        url = reverse("admin:orders_order_change", args=[obj.order.id])
        return mark_safe(f'<a href="{url}">Заказ #{obj.order.id}</a>')
