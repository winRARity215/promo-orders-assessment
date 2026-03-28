from __future__ import annotations

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model

from catalog.models import Category, Good
from orders.models import PromoCode, Order, OrderItem, PromoCodeRedemption


class PromoCodeTest(TestCase):
    
    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.category = Category.objects.create(name="Test Category")
        self.promo = PromoCode.objects.create(
            code="TEST10",
            discount_rate=Decimal("0.1"),
            category=self.category
        )
    
    def test_promo_code_creation(self) -> None:
        self.assertEqual(str(self.promo), "TEST10")
        self.assertEqual(self.promo.discount_rate, Decimal("0.1"))
        self.assertEqual(self.promo.category, self.category)
        self.assertTrue(self.promo.is_active)
    
    def test_promo_code_validation(self) -> None:
        self.promo.max_usages = 5
        self.promo.save()
        
        self.assertTrue(self.promo.is_valid())
        
        from django.utils import timezone
        import datetime
        self.promo.expires_at = timezone.now() - datetime.timedelta(days=1)
        self.promo.save()
        self.assertFalse(self.promo.is_valid())


class OrderTest(TestCase):
    
    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.order = Order.objects.create(
            user=self.user,
            price=Decimal("200.00"),
            total=Decimal("180.00")
        )
    
    def test_order_creation(self) -> None:
        self.assertEqual(str(self.order), f"Order #{self.order.id} by {self.user}")
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.price, Decimal("200.00"))
        self.assertEqual(self.order.total, Decimal("180.00"))


class OrderItemTest(TestCase):
    
    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.category = Category.objects.create(name="Test Category")
        self.good = Good.objects.create(
            name="Test Good",
            category=self.category,
            price=Decimal("100.00")
        )
        
        self.order = Order.objects.create(
            user=self.user,
            price=Decimal("200.00"),
            total=Decimal("200.00")
        )
        
        self.item = OrderItem.objects.create(
            order=self.order,
            good=self.good,
            quantity=2,
            unit_price=Decimal("100.00"),
            discount_rate=Decimal("0.1"),
            total=Decimal("180.00")
        )
    
    def test_order_item_creation(self) -> None:
        self.assertEqual(self.item.order, self.order)
        self.assertEqual(self.item.good, self.good)
        self.assertEqual(self.item.quantity, 2)
        self.assertEqual(self.item.unit_price, Decimal("100.00"))
        self.assertEqual(self.item.discount_rate, Decimal("0.1"))
        self.assertEqual(self.item.total, Decimal("180.00"))
        
        expected = f"2x {self.good} in Order #{self.order.id}"
        self.assertEqual(str(self.item), expected)


class PromoCodeRedemptionTest(TestCase):
    
    def setUp(self) -> None:
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        
        self.promo = PromoCode.objects.create(
            code="TEST10",
            discount_rate=Decimal("0.1")
        )
        
        self.order = Order.objects.create(
            user=self.user,
            price=Decimal("200.00"),
            total=Decimal("200.00")
        )
        
        self.redemption = PromoCodeRedemption.objects.create(
            promo_code=self.promo,
            user=self.user,
            order=self.order
        )
    
    def test_redemption_creation(self) -> None:
        self.assertEqual(self.redemption.promo_code, self.promo)
        self.assertEqual(self.redemption.user, self.user)
        self.assertEqual(self.redemption.order, self.order)
        
        expected = f"{self.user} used {self.promo.code} for Order #{self.order.id}"
        self.assertEqual(str(self.redemption), expected)
