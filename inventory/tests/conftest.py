from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from inventory.models import Category, Product, Supplier


@pytest.fixture()
def admin_user(db):
    return User.objects.create_user("admin", password="adminpass123", is_staff=True)


@pytest.fixture()
def employee(db):
    return User.objects.create_user("employee", password="employeepass123")


@pytest.fixture()
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    return client


@pytest.fixture()
def employee_client(employee):
    client = APIClient()
    client.force_authenticate(employee)
    return client


@pytest.fixture()
def category(db):
    return Category.objects.create(name="Beverages")


@pytest.fixture()
def supplier(db):
    return Supplier.objects.create(name="ACME", email="sales@acme.com")


@pytest.fixture()
def product(category, supplier):
    return Product.objects.create(
        sku="COF-001",
        name="Coffee 500g",
        category=category,
        supplier=supplier,
        price=Decimal("120.00"),
        stock=10,
        min_stock=5,
    )
