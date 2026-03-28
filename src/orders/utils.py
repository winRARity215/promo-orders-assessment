from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings

MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def decimal_to_str(value: Decimal) -> str:
    normalized = value.normalize()
    return format(normalized, "f")


@dataclass(frozen=True)
class GoodSnapshot:
    
    good_id: int
    category_id: int
    unit_price: Decimal
    exclude_from_promotions: bool = False


@dataclass(frozen=True)
class OrderLine:
    
    good: GoodSnapshot
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise DjangoValidationError("Количество товара должно быть положительным.", code="invalid_quantity")


class OrderCalculator:
    
    def __init__(self, user_id: int, lines: List[OrderLine], promo_code: Optional[models.PromoCode] = None):
        if user_id <= 0:
            raise DjangoValidationError("ID пользователя должен быть положительным.", code="invalid_user_id")
        if not lines:
            raise DjangoValidationError("Список товаров не может быть пустым.", code="empty_goods")
        self.user_id = user_id
        self.lines = lines
        self.promo_code = promo_code
    
    def calculate(self) -> dict:
        price = Decimal("0")
        total = Decimal("0")
        items: list[dict] = []
        eligible_found = False

        for line in self.lines:
            line_price = money(line.good.unit_price * line.quantity)
            discount_rate = Decimal("0")
            
            if self._is_line_eligible_for_promo(line):
                eligible_found = True
                discount_rate = self.promo_code.discount_rate
                line_total = money(line_price * (Decimal("1") - discount_rate))
            else:
                line_total = line_price
            
            price += line_price
            total += line_total
            items.append({
                "good_id": line.good.good_id,
                "quantity": line.quantity,
                "price": money(line.good.unit_price),
                "discount": decimal_to_str(discount_rate),
                "total": line_total,
            })

        if self.promo_code is not None and not eligible_found and self.lines:
            pass

        return {
            "user_id": self.user_id,
            "goods": items,
            "price": money(price),
            "discount": decimal_to_str(self.promo_code.discount_rate if self.promo_code else Decimal("0")),
            "total": money(total),
        }

    def _is_line_eligible_for_promo(self, line: OrderLine) -> bool:
        if self.promo_code is None:
            return False
        if line.good.exclude_from_promotions:
            return False
        if self.promo_code.category_id and line.good.category_id != self.promo_code.category_id:
            return False
        return True
