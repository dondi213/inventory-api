from django.db.models import Count, DecimalField, ExpressionWrapper, F, ProtectedError, Sum
from django.db.models.functions import Coalesce
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from inventory.models import Category, Product, StockMovement, Supplier
from inventory.permissions import IsAdminOrReadOnly
from inventory.serializers import (
    CategorySerializer,
    ProductSerializer,
    StockMovementSerializer,
    SupplierSerializer,
)
from inventory.services import register_movement


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name"]

    def destroy(self, request, *args, **kwargs):
        # Category.products uses on_delete=PROTECT: answer 409 instead of a 500 error.
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Category has products; move or delete them first."},
                status=status.HTTP_409_CONFLICT,
            )


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["name", "email"]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["sku", "name"]
    ordering_fields = ["name", "price", "stock", "created_at"]

    def get_queryset(self):
        # select_related avoids one extra query per product (N+1 problem).
        qs = Product.objects.select_related("category", "supplier")
        params = self.request.query_params

        if category := params.get("category"):
            qs = qs.filter(category_id=category)
        if supplier := params.get("supplier"):
            qs = qs.filter(supplier_id=supplier)
        if params.get("is_active") in ("true", "false"):
            qs = qs.filter(is_active=params["is_active"] == "true")
        if params.get("low_stock") == "true":
            qs = qs.filter(stock__lte=F("min_stock"))
        return qs


class StockMovementViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Movements are an audit log: they can be created and read, never edited or deleted."""

    serializer_class = StockMovementSerializer
    ordering_fields = ["created_at"]

    def get_queryset(self):
        qs = StockMovement.objects.select_related("product", "created_by")
        if product := self.request.query_params.get("product"):
            qs = qs.filter(product_id=product)
        if movement_type := self.request.query_params.get("type"):
            qs = qs.filter(movement_type=movement_type.upper())
        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        movement = register_movement(
            product_id=data["product"].id,
            movement_type=data["movement_type"],
            quantity=data["quantity"],
            note=data.get("note", ""),
            user=request.user,
        )
        return Response(self.get_serializer(movement).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def inventory_summary(request):
    """Aggregated report computed in the database (not in Python loops)."""
    stock_value = ExpressionWrapper(
        F("price") * F("stock"), output_field=DecimalField(max_digits=14, decimal_places=2)
    )
    active = Product.objects.filter(is_active=True)

    totals = active.aggregate(
        total_products=Count("id"),
        total_units=Coalesce(Sum("stock"), 0),
        total_value=Coalesce(Sum(stock_value), 0, output_field=DecimalField()),
    )
    by_category = (
        active.values(category_name=F("category__name"))
        .annotate(products=Count("id"), units=Coalesce(Sum("stock"), 0), value=Sum(stock_value))
        .order_by("category_name")
    )
    low_stock = active.filter(stock__lte=F("min_stock")).values(
        "id", "sku", "name", "stock", "min_stock"
    )

    return Response(
        {
            **totals,
            "low_stock_count": low_stock.count(),
            "low_stock_products": list(low_stock),
            "by_category": list(by_category),
        }
    )
