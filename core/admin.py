from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin, GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.models import Group
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Region, Location, Vendor, Product, Stock, DeliveryEntry, Expense

User = get_user_model()


@admin.register(Region)
class RegionAdmin(ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    search_fields = ['name']


@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ['name', 'region', 'contact', 'is_active', 'created_at']
    list_filter = ['region', 'is_active']
    search_fields = ['name', 'contact']


@admin.register(User)
class UserAdmin(DjangoUserAdmin, ModelAdmin):
    """Lets the master superuser create users and assign role/region/locations."""
    # Unfold-styled auth forms
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ['username', 'role', 'region', 'location', 'is_staff', 'is_superuser']
    list_filter = ['role', 'region', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    filter_horizontal = ['assigned_locations', 'groups', 'user_permissions']
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Role & Access', {
            'fields': ('role', 'region', 'location', 'assigned_locations'),
        }),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Role & Access', {
            'fields': ('role', 'region', 'location', 'assigned_locations'),
        }),
    )


# Re-register Group with Unfold styling.
admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin, ModelAdmin):
    pass


@admin.register(Vendor)
class VendorAdmin(ModelAdmin):
    list_display = ['name', 'contact', 'location', 'user', 'created_at']
    list_filter = ['location']
    search_fields = ['name', 'contact']


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'vendor', 'price', 'location', 'created_at']
    list_filter = ['location']
    search_fields = ['name', 'vendor__name']


@admin.register(Stock)
class StockAdmin(ModelAdmin):
    list_display = ['product', 'quantity', 'location', 'last_updated', 'updated_by']
    list_filter = ['location', 'last_updated']


@admin.register(DeliveryEntry)
class DeliveryEntryAdmin(ModelAdmin):
    list_display = ['product', 'vendor', 'quantity', 'price', 'delivery_fee', 'date', 'location', 'created_by']
    list_filter = ['date', 'location', 'vendor']
    search_fields = ['product__name', 'vendor__name']


@admin.register(Expense)
class ExpenseAdmin(ModelAdmin):
    list_display = ['description', 'amount', 'date', 'location', 'created_by']
    list_filter = ['date', 'location']
