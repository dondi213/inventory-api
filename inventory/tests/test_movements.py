from decimal import Decimal

import pytest

from inventory.models import Product, StockMovement

pytestmark = pytest.mark.django_db


def post_movement(client, product, movement_type, quantity, note=""):
    return client.post(
        "/api/movements/",
        {"product": product.id, "movement_type": movement_type, "quantity": quantity, "note": note},
        format="json",
    )


def test_stock_in_increases_stock(employee_client, product):
    res = post_movement(employee_client, product, "IN", 5, "Supplier delivery")
    assert res.status_code == 201, res.json()
    assert res.json()["created_by"] == "employee"
    product.refresh_from_db()
    assert product.stock == 15


def test_stock_out_decreases_stock(employee_client, product):
    assert post_movement(employee_client, product, "OUT", 4).status_code == 201
    product.refresh_from_db()
    assert product.stock == 6


def test_stock_out_cannot_go_negative(employee_client, product):
    res = post_movement(employee_client, product, "OUT", 11)
    assert res.status_code == 400
    assert "Insufficient stock" in str(res.json())
    product.refresh_from_db()
    assert product.stock == 10
    assert StockMovement.objects.count() == 0  # nothing saved


def test_zero_quantity_rejected(employee_client, product):
    assert post_movement(employee_client, product, "IN", 0).status_code == 400


def test_invalid_type_rejected(employee_client, product):
    assert post_movement(employee_client, product, "MOVE", 1).status_code == 400


def test_inactive_product_rejected(employee_client, product):
    product.is_active = False
    product.save()
    assert post_movement(employee_client, product, "IN", 1).status_code == 400


def test_movements_cannot_be_edited_or_deleted(employee_client, product):
    movement_id = post_movement(employee_client, product, "IN", 1).json()["id"]
    assert employee_client.delete(f"/api/movements/{movement_id}/").status_code == 405
    assert (
        employee_client.patch(f"/api/movements/{movement_id}/", {"quantity": 9}).status_code == 405
    )


def test_filter_movements_by_type(employee_client, product):
    post_movement(employee_client, product, "IN", 3)
    post_movement(employee_client, product, "OUT", 1)
    res = employee_client.get("/api/movements/?type=out")
    assert [m["movement_type"] for m in res.json()["results"]] == ["OUT"]


def test_summary_report(employee_client, product, category):
    Product.objects.create(
        sku="COF-002", name="Coffee 1kg", category=category, price=Decimal("200"), stock=2
    )
    data = employee_client.get("/api/reports/summary/").json()

    assert data["total_products"] == 2
    assert data["total_units"] == 12
    assert Decimal(str(data["total_value"])) == Decimal("1600.00")  # 120*10 + 200*2
    assert data["low_stock_count"] == 1
    assert data["low_stock_products"][0]["sku"] == "COF-002"
    assert data["by_category"][0]["category_name"] == "Beverages"
