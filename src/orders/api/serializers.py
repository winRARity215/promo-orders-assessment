from __future__ import annotations

from decimal import Decimal
from rest_framework import serializers
from catalog.models import Good
from orders.models import Order, OrderItem, PromoCode


class OrderGoodInSerializer(serializers.Serializer):
    
    good_id = serializers.IntegerField(
        min_value=1,
        error_messages={"required": "Поле good_id обязательно."}
    )
    quantity = serializers.IntegerField(
        min_value=1,
        error_messages={"required": "Поле quantity обязательно."}
    )


class OrderCreateRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(
        min_value=1,
        error_messages={"required": "Поле user_id обязательно."}
    )
    goods = OrderGoodInSerializer(many=True)
    promo_code = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        allow_null=True
    )

    def validate_goods(self, value: list[dict]) -> list[dict]:
        if not value:
            raise serializers.ValidationError("Поле goods обязательно и не должно быть пустым.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    
    price = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        read_only=True
    )
    discount = serializers.SerializerMethodField()
    total = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ["good_id", "quantity", "price", "discount", "total"]
        read_only_fields = ["total"]
    
    def get_discount(self, obj: OrderItem) -> str:
        return str(obj.discount_rate)


class OrderSerializer(serializers.ModelSerializer):
    
    order_id = serializers.IntegerField(source="id", read_only=True)
    goods = OrderItemSerializer(source="items", many=True, read_only=True)
    price = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        read_only=True
    )
    discount = serializers.SerializerMethodField()
    total = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        read_only=True
    )
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = ["order_id", "user_id", "price", "discount", "total", "created_at"]
        read_only_fields = ["user_id", "price", "total", "created_at"]
    
    def get_discount(self, obj: Order) -> str:
        return str(obj.discount_rate)


class PromoCodeSerializer(serializers.ModelSerializer):
    
    usage_count = serializers.SerializerMethodField()
    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = ["code", "discount_rate", "category", "max_usages", "usage_count", "is_valid", "created_at"]
        read_only_fields = ["created_at"]
    
    def get_usage_count(self, obj: PromoCode) -> int:
        return obj.orders.count()
    
    def get_is_valid(self, obj: PromoCode) -> bool:
        return obj.is_valid()
