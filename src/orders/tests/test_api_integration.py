from __future__ import annotations

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from catalog.models import Category, Good
from orders.models import PromoCode, Order


User = get_user_model()


class OrderApiIntegrationTests(TestCase):
    
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        self.category = Category.objects.create(name="Electronics")
        self.good1 = Good.objects.create(
            name="Laptop", 
            category=self.category, 
            price=Decimal("1000.00"),
            exclude_from_promotions=False
        )
        self.good2 = Good.objects.create(
            name="Premium Laptop", 
            category=self.category, 
            price=Decimal("1500.00"),
            exclude_from_promotions=True
        )
        
        self.promo = PromoCode.objects.create(
            code="TEST2025",
            discount_rate=Decimal("0.15"),
            max_usages=10,
            is_active=True
        )
    
    def test_create_order_without_promo(self) -> None:
        data = {
            "user_id": self.user.id,
            "goods": [
                {"good_id": self.good1.id, "quantity": 2}
            ]
        }
        
        response = self.client.post("/api/orders/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        
        self.assertEqual(result["user_id"], self.user.id)
        self.assertEqual(len(result["goods"]), 1)
        self.assertEqual(result["goods"][0]["good_id"], self.good1.id)
        self.assertEqual(result["goods"][0]["quantity"], 2)
        self.assertEqual(result["goods"][0]["price"], 1000.0)
        self.assertEqual(result["goods"][0]["discount"], "0.0000")
        self.assertEqual(result["goods"][0]["total"], 2000.0)
        self.assertEqual(result["price"], "2000.00")
        self.assertEqual(result["discount"], "0")
        self.assertEqual(result["total"], "2000.00")
    
    def test_create_order_with_valid_promo(self) -> None:
        data = {
            "user_id": self.user.id,
            "goods": [
                {"good_id": self.good1.id, "quantity": 1}
            ],
            "promo_code": "TEST2025"
        }
        
        response = self.client.post("/api/orders/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        
        self.assertEqual(result["price"], "1000.00")
        self.assertEqual(result["discount"], "0.15")
        self.assertEqual(result["total"], "850.00")
        self.assertEqual(result["goods"][0]["discount"], "0.1500")
        self.assertEqual(result["goods"][0]["total"], 850.0)
    
    def test_create_order_with_invalid_promo(self) -> None:
        data = {
            "user_id": self.user.id,
            "goods": [
                {"good_id": self.good1.id, "quantity": 1}
            ],
            "promo_code": "INVALID"
        }
        
        response = self.client.post("/api/orders/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Промокод не найден", response.json()["error"])
    
    def test_create_order_with_excluded_good_and_promo(self) -> None:
        data = {
            "user_id": self.user.id,
            "goods": [
                {"good_id": self.good2.id, "quantity": 1}
            ],
            "promo_code": "TEST2025"
        }
        
        response = self.client.post("/api/orders/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        
        self.assertEqual(result["goods"][0]["discount"], "0.0000")
        self.assertEqual(result["goods"][0]["total"], 1500.0)
        self.assertEqual(result["discount"], "0.15")
        self.assertEqual(result["total"], "1500.00")
    
    def test_create_order_multiple_goods_with_promo(self) -> None:
        data = {
            "user_id": self.user.id,
            "goods": [
                {"good_id": self.good1.id, "quantity": 1},
                {"good_id": self.good2.id, "quantity": 1}
            ],
            "promo_code": "TEST2025"
        }
        
        response = self.client.post("/api/orders/", data, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        result = response.json()
        
        self.assertEqual(len(result["goods"]), 2)
        self.assertEqual(result["price"], "2500.00")
        self.assertEqual(result["total"], "2350.00")
