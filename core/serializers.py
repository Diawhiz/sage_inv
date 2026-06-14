from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Location, Vendor, Product, Stock, MissingStock, MissingStockLog, DeliveryEntry, Expense

User = get_user_model()


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'contact', 'is_active', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'role_display',
            'is_superuser', 'is_staff', 'location', 'location_name',
            'is_ceo', 'is_coo', 'is_cto', 'is_manager',
            'has_location_access', 'can_access_operations',
            'can_access_calculations', 'can_access_missing_stock',
            'can_register_users',
        ]
        read_only_fields = [
            'id', 'is_superuser', 'is_staff',
            'is_ceo', 'is_coo', 'is_cto', 'is_manager',
            'has_location_access', 'can_access_operations',
            'can_access_calculations', 'can_access_missing_stock',
            'can_register_users',
        ]


class VendorSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Vendor
        fields = ['id', 'name', 'contact', 'address', 'location', 'location_name', 'user']
        read_only_fields = ['user']


class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price',
            'vendor', 'vendor_name', 'location', 'location_name',
        ]


class StockSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Stock
        fields = [
            'id', 'product', 'product_name', 'quantity',
            'last_updated', 'updated_by', 'updated_by_username',
            'location', 'location_name',
        ]
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
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = MissingStock
        fields = [
            'id', 'product', 'product_name', 'quantity_missing',
            'date_reported', 'action_taken', 'logs',
            'location', 'location_name',
        ]
        read_only_fields = ['date_reported']


class DeliveryEntrySerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = DeliveryEntry
        fields = [
            'id', 'vendor', 'vendor_name', 'product', 'product_name',
            'price', 'delivery_fee', 'quantity', 'rider',
            'delivery_location', 'date',
            'created_by', 'created_by_username',
            'location', 'location_name',
        ]
        read_only_fields = ['created_by']

    def validate(self, data):
        product = data.get('product')
        vendor = data.get('vendor')
        if product and vendor and product.vendor_id != vendor.id:
            raise serializers.ValidationError(
                {'product': 'This product does not belong to the selected vendor.'}
            )
        return data


class ExpenseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'description', 'amount', 'date',
            'created_by', 'created_by_username',
            'location', 'location_name',
        ]
        read_only_fields = ['created_by']
