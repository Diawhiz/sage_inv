from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Region, Location, Vendor, Product, Stock, DeliveryEntry, Expense

User = get_user_model()


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'is_active', 'created_at']


class LocationSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = Location
        fields = ['id', 'name', 'address', 'contact', 'region', 'region_name', 'is_active', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'role_display',
            'is_superuser', 'is_staff',
            'location', 'location_name', 'region', 'region_name',
            'assigned_locations',
            'is_ceo', 'is_coo', 'is_cto', 'is_cfo',
            'is_regional_manager', 'is_manager', 'is_agent',
            'has_location_access', 'can_access_operations',
            'can_access_calculations', 'can_view_stock',
            'can_register_users',
        ]
        read_only_fields = [
            'id', 'is_superuser', 'is_staff',
            'is_ceo', 'is_coo', 'is_cto', 'is_cfo',
            'is_regional_manager', 'is_manager', 'is_agent',
            'has_location_access', 'can_access_operations',
            'can_access_calculations', 'can_view_stock',
            'can_register_users',
        ]


class VendorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vendor
        fields = ['id', 'name', 'contact', 'address', 'user']
        read_only_fields = ['user']


class ProductSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price',
            'vendor', 'vendor_name',
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
