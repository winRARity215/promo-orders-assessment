from __future__ import annotations

from decimal import Decimal
from typing import List, Dict, Any, Optional

from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from catalog.models import Good
from .models import Order, OrderItem, PromoCode, PromoCodeRedemption
from .utils import OrderCalculator, GoodSnapshot, OrderLine


class OrderService:
    
    @staticmethod
    def create_order(user_id: int, goods: List[dict], promo_code: Optional[str] = None) -> Order:
        from catalog.models import Good, Category
        
        promo_obj = None
        if promo_code:
            try:
                promo_obj = PromoCode.objects.get(code=promo_code)
                if promo_obj and not promo_obj.can_be_used_by_user(user_id):
                    raise DjangoValidationError("Промокод уже был использован этим пользователем.")
                if not promo_obj.is_valid():
                    raise DjangoValidationError("Промокод недействителен или истёк.")
            except PromoCode.DoesNotExist:
                raise DjangoValidationError("Промокод не найден.")
        
        good_ids = [item["good_id"] for item in goods]
        goods_qs = Good.objects.filter(id__in=good_ids).select_related("category")
        goods_map = {good.id: good for good in goods_qs}
        
        lines = []
        for item in goods:
            good = goods_map.get(item["good_id"])
            if not good:
                raise DjangoValidationError(f"Товар с ID {item['good_id']} не найден.")
            
            lines.append(OrderLine(
                good=GoodSnapshot(
                    good_id=good.id,
                    category_id=good.category_id,
                    unit_price=good.price,
                    exclude_from_promotions=good.exclude_from_promotions
                ),
                quantity=item["quantity"]
            ))
        
        calculator = OrderCalculator(user_id=user_id, lines=lines, promo_code=promo_obj)
        calculation = calculator.calculate()
        
        order = Order.objects.create(
            user_id=user_id,
            promo_code=promo_obj,
            price=calculation["price"],
            discount_rate=Decimal(calculation["discount"]),
            total=calculation["total"]
        )
        
        for item_data in calculation["goods"]:
            OrderItem.objects.create(
                order=order,
                good_id=item_data["good_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["price"],
                discount_rate=Decimal(item_data["discount"]),
                total=item_data["total"]
            )
        
        if promo_obj:
            try:
                PromoCodeRedemption.objects.create(
                    promo_code=promo_obj,
                    user_id=user_id,
                    order=order
                )
            except Exception:
                pass
        
        return order
    
    @staticmethod
    def get_order_data(order: Order) -> Dict[str, Any]:
        items = []
        for item in order.items.all():
            items.append({
                "good_id": item.good_id,
                "quantity": item.quantity,
                "price": item.unit_price,
                "discount": str(item.discount_rate),
                "total": item.total,
            })
        
        return {
            "order_id": order.id,
            "user_id": order.user_id,
            "goods": items,
            "price": str(order.price),
            "discount": str(order.discount_rate),
            "total": str(order.total),
            "created_at": order.created_at.isoformat(),
        }
