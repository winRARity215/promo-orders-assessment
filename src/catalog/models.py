from __future__ import annotations

from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self) -> str:
        return self.name


class Good(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="goods")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    exclude_from_promotions = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name
