from rest_framework import serializers

from inventory.models import Category, Product, StockMovement, Supplier


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "email", "phone"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "sku",
            "name",
            "description",
            "category",
            "category_name",
            "supplier",
            "price",
            "stock",
            "min_stock",
            "is_low_stock",
            "is_active",
            "created_at",
            "updated_at",
        ]
        # Stock can only change through stock movements.
        read_only_fields = ["stock", "created_at", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    created_by = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "product_sku",
            "movement_type",
            "quantity",
            "note",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate_product(self, product: Product) -> Product:
        if not product.is_active:
            raise serializers.ValidationError("Product is inactive.")
        return product
