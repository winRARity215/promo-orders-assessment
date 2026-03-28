from __future__ import annotations

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class PromoCode(models.Model):
    
    code = models.CharField(max_length=50, unique=True)
    discount_rate = models.DecimalField(max_digits=6, decimal_places=4)
    category = models.ForeignKey("catalog.Category", on_delete=models.CASCADE, null=True, blank=True, related_name="promo_codes")
    max_usages = models.PositiveIntegerField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(discount_rate__gt=0) & models.Q(discount_rate__lte=1),
                name="valid_discount_rate"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def clean(self) -> None:
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError("Промокод истёк.")
        if self.discount_rate <= 0 or self.discount_rate > 1:
            raise ValidationError("Скидка должна быть в диапазоне от 0 до 1.")

    def is_valid(self) -> bool:
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        if self.max_usages and self.orders.count() >= self.max_usages:
            return False
        return True

    def can_be_used_by_user(self, user: settings.AUTH_USER_MODEL) -> bool:
        if not self.is_valid():
            return False
        return not self.redemptions.filter(user=user).exists()


class Order(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")
    promo_code = models.ForeignKey(PromoCode, on_delete=models.PROTECT, null=True, blank=True, related_name="orders")
    discount_rate = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0"))
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Order #{self.id} by {self.user}"


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    good = models.ForeignKey("catalog.Good", on_delete=models.PROTECT, related_name="order_items")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_rate = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = [["order", "good"]]

    def __str__(self) -> str:
        return f"{self.quantity}x {self.good} in Order #{self.order.id}"


class PromoCodeRedemption(models.Model):

    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="redemptions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="promo_redemptions")
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="promo_redemption")
    redeemed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["promo_code", "user"], name="uniq_promo_per_user"),
        ]
        ordering = ["-redeemed_at"]

    def __str__(self) -> str:
        return f"{self.user} used {self.promo_code.code} for Order #{self.order.id}"
