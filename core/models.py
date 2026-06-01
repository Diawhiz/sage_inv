from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import datetime


class User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_permissions_set',
        blank=True
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.username


class Vendor(models.Model):
    name = models.CharField(max_length=200)
    contact = models.CharField(max_length=100)
    address = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Stock(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock')
    quantity = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"


class MissingStock(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='missing_reports')
    quantity_missing = models.IntegerField()
    date_reported = models.DateTimeField(auto_now_add=True)
    action_taken = models.TextField(blank=True)

    def __str__(self):
        return f"{self.product.name} - Missing: {self.quantity_missing}"


class MissingStockLog(models.Model):
    missing_stock = models.ForeignKey(MissingStock, on_delete=models.CASCADE, related_name='logs')
    quantity = models.IntegerField()
    note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['updated_at']

    def __str__(self):
        return f"{self.missing_stock.product.name} — {self.quantity} @ {self.updated_at:%Y-%m-%d %H:%M}"


class DeliveryEntry(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='deliveries')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='deliveries')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    rider = models.CharField(max_length=200, blank=True)
    location = models.CharField(max_length=300, blank=True)
    date = models.DateField(default=datetime.date.today)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.product.name} x{self.quantity} on {self.date}"


class Expense(models.Model):
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=datetime.date.today)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.description}: {self.amount}"
