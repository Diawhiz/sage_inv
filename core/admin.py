from django.contrib import admin
from .models import Vendor, Product, Stock, MissingStock

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact', 'user', 'created_at']
    search_fields = ['name', 'contact']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'created_at']
    search_fields = ['name', 'vendor__name']

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity', 'last_updated', 'updated_by']
    list_filter = ['last_updated']

@admin.register(MissingStock)
class MissingStockAdmin(admin.ModelAdmin):
    list_display = ['product', 'quantity_missing', 'date_reported']
    list_filter = ['date_reported']