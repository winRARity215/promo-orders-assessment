from __future__ import annotations

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils import timezone

from catalog.models import Category, Good
from orders.models import PromoCode


class CreateOrderApiTests(TestCase):

    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(username="u1", password="x")

        self.cat_a = Category.objects.create(name="A")
        self.cat_b = Category.objects.create(name="B")
        self.good_a = Good.objects.create(name="GA", category=self.cat_a, price="100.00")
        self.good_b = Good.objects.create(name="GB", category=self.cat_b, price="50.00")
        self.good_excluded = Good.objects.create(
            name="GX", category=self.cat_a, price="10.00", exclude_from_promotions=True
        )
        self.client = Client()

    def test_create_without_promo(self) -> None:
        resp = self.client.post(
            "/api/orders/",
            data=json.dumps(
                {
                    "user_id": self.user.id,
                    "goods": [{"good_id": self.good_a.id, "quantity": 2}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        data = resp.json()
        self.assertEqual(float(data["price"]), 200)
        self.assertEqual(data["discount"], "0")
        self.assertEqual(float(data["total"]), 200)

    def test_promo_applies_only_to_category_and_not_excluded_goods(self) -> None:
        PromoCode.objects.create(
            code="PROMO10",
            discount_rate=Decimal("0.1"),
            expires_at=timezone.now() + timezone.timedelta(days=1),
            category=self.cat_a,
        )
        resp = self.client.post(
            "/api/orders/",
            data=json.dumps(
                {
                    "user_id": self.user.id,
                    "goods": [
                        {"good_id": self.good_a.id, "quantity": 1},
                        {"good_id": self.good_b.id, "quantity": 1},
                        {"good_id": self.good_excluded.id, "quantity": 1},
                    ],
                    "promo_code": "PROMO10",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        data = resp.json()
        self.assertEqual(float(data["price"]), 160)
        self.assertEqual(float(data["total"]), 150)

    def test_promo_reuse_by_same_user_is_forbidden(self) -> None:
        PromoCode.objects.create(code="PROMO10", discount_rate=Decimal("0.1"))
        payload = {
            "user_id": self.user.id,
            "goods": [{"good_id": self.good_a.id, "quantity": 1}],
            "promo_code": "PROMO10",
        }
        resp1 = self.client.post("/api/orders/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp1.status_code, 201, resp1.content)
        resp2 = self.client.post("/api/orders/", data=json.dumps(payload), content_type="application/json")
        self.assertEqual(resp2.status_code, 400, resp2.content)
        self.assertIn("Промокод уже был использован этим пользователем.", resp2.json()["error"])
