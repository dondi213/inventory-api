from django.contrib import admin

from inventory.models import Category, Product, StockMovement, Supplier


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("sku", "name", "category", "price", "stock", "min_stock", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("sku", "name")
    readonly_fields = ("stock",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity", "created_by", "created_at")
    list_filter = ("movement_type",)


admin.site.register(Category)
admin.site.register(Supplier)
