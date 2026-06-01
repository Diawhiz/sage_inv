from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Vendor, Product, Stock, MissingStock, MissingStockLog, DeliveryEntry, Expense

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
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
        fields = ['id', 'name', 'description', 'price', 'vendor', 'vendor_name']


class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = Stock
        fields = ['id', 'product', 'product_name', 'quantity', 'last_updated', 'updated_by', 'updated_by_username']
        read_only_fields = ['last_updated', 'updated_by']


class MissingStockLogSerializer(serializers.ModelSerializer):
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = MissingStockLog
        fields = ['id', 'quantity', 'note', 'updated_at', 'updated_by_username']
        read_only_fields = ['updated_at', 'updated_by_username']


class MissingStockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    logs = MissingStockLogSerializer(many=True, read_only=True)

    class Meta:
        model = MissingStock
        fields = ['id', 'product', 'product_name', 'quantity_missing', 'date_reported', 'action_taken', 'logs']
        read_only_fields = ['date_reported']


class DeliveryEntrySerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = DeliveryEntry
        fields = [
            'id', 'vendor', 'vendor_name', 'product', 'product_name',
            'price', 'delivery_fee', 'quantity', 'rider', 'location', 'date',
            'created_by', 'created_by_username',
        ]
        read_only_fields = ['created_by']

    def validate(self, data):
        product = data.get('product')
        vendor = data.get('vendor')
        if product and vendor and product.vendor_id != vendor.id:
            raise serializers.ValidationError({'product': 'This product does not belong to the selected vendor.'})
        return data


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'description', 'amount', 'date', 'created_by', 'created_by_username']
        read_only_fields = ['created_by']
