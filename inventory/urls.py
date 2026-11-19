from django.urls import include, path
from rest_framework.routers import DefaultRouter

from inventory import views

router = DefaultRouter()
router.register("categories", views.CategoryViewSet)
router.register("suppliers", views.SupplierViewSet)
router.register("products", views.ProductViewSet, basename="product")
router.register("movements", views.StockMovementViewSet, basename="movement")

urlpatterns = [
    path("reports/summary/", views.inventory_summary, name="inventory-summary"),
    path("", include(router.urls)),
]
