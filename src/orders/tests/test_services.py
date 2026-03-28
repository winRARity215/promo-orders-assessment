from __future__ import annotations

from decimal import Decimal
from unittest.mock import Mock
from django.test import TestCase
from django.core.exceptions import ValidationError as DjangoValidationError

from orders.utils import GoodSnapshot, OrderLine, OrderCalculator
from orders.services import OrderService


class OrderCalculatorTest(TestCase):
    
    def test_calculator_no_promo(self) -> None:
        good = GoodSnapshot(
            good_id=1,
            category_id=1,
            unit_price=Decimal("100.00"),
            exclude_from_promotions=False
        )
        line = OrderLine(good=good, quantity=2)
        
        calculator = OrderCalculator(user_id=1, lines=[line], promo_code=None)
        result = calculator.calculate()
        
        self.assertEqual(result["user_id"], 1)
        self.assertEqual(len(result["goods"]), 1)
        self.assertEqual(result["goods"][0]["good_id"], 1)
        self.assertEqual(result["goods"][0]["quantity"], 2)
        self.assertEqual(str(result["goods"][0]["price"]), "100.00")
        self.assertEqual(result["goods"][0]["discount"], "0")
        self.assertEqual(str(result["goods"][0]["total"]), "200.00")
        self.assertEqual(str(result["price"]), "200.00")
        self.assertEqual(result["discount"], "0")
        self.assertEqual(str(result["total"]), "200.00")
    
    def test_calculator_with_promo(self) -> None:
        good = GoodSnapshot(
            good_id=1,
            category_id=1,
            unit_price=Decimal("100.00"),
            exclude_from_promotions=False
        )
        line = OrderLine(good=good, quantity=2)
        
        promo = Mock()
        promo.discount_rate = Decimal("0.1")
        promo.category_id = None
        
        calculator = OrderCalculator(user_id=1, lines=[line], promo_code=promo)
        result = calculator.calculate()
        
        self.assertEqual(result["discount"], "0.1")
        self.assertEqual(str(result["total"]), "180.00")
    
    def test_calculator_category_restriction(self) -> None:
        promo = Mock()
        promo.discount_rate = Decimal("0.1")
        promo.category_id = 2
        
        wrong_category_good = GoodSnapshot(
            good_id=3,
            category_id=1,
            unit_price=Decimal("100.00"),
            exclude_from_promotions=False
        )
        wrong_line = OrderLine(good=wrong_category_good, quantity=1)
        
        calculator = OrderCalculator(user_id=1, lines=[wrong_line], promo_code=None)
        
        result = calculator.calculate()
        self.assertEqual(result["discount"], "0")
        self.assertEqual(result["total"], Decimal("100.00"))
    
    def test_calculator_empty_goods(self) -> None:
        with self.assertRaises(DjangoValidationError) as cm:
            OrderCalculator(user_id=1, lines=[], promo_code=None)
        self.assertEqual(cm.exception.code, "empty_goods")
    
    def test_calculator_invalid_user_id(self) -> None:
        good = GoodSnapshot(
            good_id=1,
            category_id=1,
            unit_price=Decimal("100.00"),
            exclude_from_promotions=False
        )
        line = OrderLine(good=good, quantity=1)
        
        with self.assertRaises(DjangoValidationError) as cm:
            OrderCalculator(user_id=0, lines=[line], promo_code=None)
        self.assertEqual(cm.exception.code, "invalid_user_id")
    
    def test_calculator_invalid_quantity(self) -> None:
        good = GoodSnapshot(
            good_id=1,
            category_id=1,
            unit_price=Decimal("100.00"),
            exclude_from_promotions=False
        )
        
        with self.assertRaises(DjangoValidationError) as cm:
            OrderLine(good=good, quantity=0)
        self.assertEqual(cm.exception.code, "invalid_quantity")


class OrderServiceTest(TestCase):
    
    def setUp(self) -> None:
        from django.contrib.auth import get_user_model
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        from catalog.models import Category
        self.category = Category.objects.create(name="Test Category")
    
    def test_create_order_without_promo(self) -> None:
        from catalog.models import Good
        good = Good.objects.create(
            name="Test Good",
            category=self.category,
            price=Decimal("100.00")
        )
        
        order = OrderService.create_order(
            user_id=self.user.id,
            goods=[{"good_id": good.id, "quantity": 2}],
            promo_code=None
        )
        
        self.assertEqual(order.user_id, self.user.id)
        self.assertEqual(order.price, Decimal("200.00"))
        self.assertEqual(order.total, Decimal("200.00"))
        self.assertEqual(order.items.count(), 1)
        
        item = order.items.first()
        self.assertEqual(item.good_id, good.id)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("100.00"))
        self.assertEqual(item.discount_rate, Decimal("0"))
        self.assertEqual(item.total, Decimal("200.00"))
    
    def test_create_order_with_promo(self) -> None:
        from catalog.models import Good
        from orders.models import PromoCode
        
        good = Good.objects.create(
            name="Test Good",
            category=self.category,
            price=Decimal("100.00")
        )
        
        promo = PromoCode.objects.create(
            code="TEST10",
            discount_rate=Decimal("0.1")
        )
        
        order = OrderService.create_order(
            user_id=self.user.id,
            goods=[{"good_id": good.id, "quantity": 2}],
            promo_code="TEST10"
        )
        
        self.assertEqual(order.user_id, self.user.id)
        self.assertEqual(order.price, Decimal("200.00"))
        self.assertEqual(order.total, Decimal("180.00"))
        self.assertEqual(order.items.count(), 1)
        
        item = order.items.first()
        self.assertEqual(item.good_id, good.id)
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.unit_price, Decimal("100.00"))
        self.assertEqual(item.discount_rate, Decimal("0.1"))
        self.assertEqual(item.total, Decimal("180.00"))
