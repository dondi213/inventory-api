from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from inventory.models import Product

pytestmark = pytest.mark.django_db


def test_health():
    assert APIClient().get("/health/").json() == {"status": "ok"}


def test_requires_authentication():
    assert APIClient().get("/api/products/").status_code == 401


def test_token_login(admin_user):
    res = APIClient().post(
        "/api/auth/token/", {"username": "admin", "password": "adminpass123"}, format="json"
    )
    assert res.status_code == 200
    assert "token" in res.json()


def test_admin_can_create_product(admin_client, category):
    res = admin_client.post(
        "/api/products/",
        {"sku": "TEA-001", "name": "Green tea", "category": category.id, "price": "45.50"},
        format="json",
    )
    assert res.status_code == 201, res.json()
    assert res.json()["stock"] == 0


def test_employee_cannot_create_product(employee_client, category):
    res = employee_client.post(
        "/api/products/",
        {"sku": "TEA-001", "name": "Green tea", "category": category.id, "price": "45.50"},
        format="json",
    )
    assert res.status_code == 403


def test_employee_can_list_products(employee_client, product):
    res = employee_client.get("/api/products/")
    assert res.status_code == 200
    assert res.json()["count"] == 1
    assert res.json()["results"][0]["category_name"] == "Beverages"


def test_stock_is_read_only(admin_client, product):
    res = admin_client.patch(f"/api/products/{product.id}/", {"stock": 999}, format="json")
    assert res.status_code == 200
    product.refresh_from_db()
    assert product.stock == 10


def test_duplicate_sku_rejected(admin_client, product, category):
    res = admin_client.post(
        "/api/products/",
        {"sku": "COF-001", "name": "Other", "category": category.id, "price": "1.00"},
        format="json",
    )
    assert res.status_code == 400


def test_negative_price_rejected(admin_client, category):
    res = admin_client.post(
        "/api/products/",
        {"sku": "X-1", "name": "X", "category": category.id, "price": "-5"},
        format="json",
    )
    assert res.status_code == 400


def test_filter_low_stock(employee_client, product, category):
    Product.objects.create(
        sku="COF-002", name="Coffee 1kg", category=category, price=Decimal("200"), stock=2
    )
    res = employee_client.get("/api/products/?low_stock=true")
    assert [p["sku"] for p in res.json()["results"]] == ["COF-002"]


def test_search_by_name(employee_client, product):
    assert employee_client.get("/api/products/?search=coffee").json()["count"] == 1
    assert employee_client.get("/api/products/?search=tea").json()["count"] == 0


def test_cannot_delete_category_with_products(admin_client, product):
    res = admin_client.delete(f"/api/categories/{product.category_id}/")
    assert res.status_code == 409


def test_delete_empty_category(admin_client):
    category_id = admin_client.post("/api/categories/", {"name": "Empty"}, format="json").json()[
        "id"
    ]
    assert admin_client.delete(f"/api/categories/{category_id}/").status_code == 204
