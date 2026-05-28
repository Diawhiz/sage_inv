from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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