from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vendor, Product, Stock, MissingStock

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Explicitly list fields — exclude groups and user_permissions
        fields = ['id', 'username', 'email', 'is_superuser', 'is_staff']
        read_only_fields = ['id', 'is_superuser', 'is_staff']


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'contact', 'address', 'user']
        read_only_fields = ['user']


class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'vendor', 'vendor_name']


class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = Stock
        fields = ['id', 'product', 'product_name', 'quantity', 'last_updated', 'updated_by', 'updated_by_username']
        read_only_fields = ['last_updated', 'updated_by']


class MissingStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = MissingStock
        fields = ['id', 'product', 'product_name', 'quantity_missing', 'date_reported', 'action_taken']
        read_only_fields = ['date_reported']