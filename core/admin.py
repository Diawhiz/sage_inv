from django.contrib import admin
from .models import Vendor, Product, Stock, MissingStock, MissingStockLog, DeliveryEntry, Expense


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'user', 'created_at']
    search_fields = ['name', 'contact']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'price', 'created_at']
    search_fields = ['name', 'vendor__name']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'last_updated', 'updated_by']
    list_filter = ['last_updated']


@admin.register(MissingStock)
class MissingStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_missing', 'date_reported']
    list_filter = ['date_reported']


@admin.register(MissingStockLog)
class MissingStockLogAdmin(admin.ModelAdmin):
    list_display = ['missing_stock', 'quantity', 'updated_at', 'updated_by']
    list_filter = ['updated_at']


@admin.register(DeliveryEntry)
class DeliveryEntryAdmin(admin.ModelAdmin):
    list_display = ['product', 'vendor', 'quantity', 'price', 'delivery_fee', 'date', 'created_by']
    list_filter = ['date', 'vendor']
    search_fields = ['product__name', 'vendor__name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'date', 'created_by']
    list_filter = ['date']
