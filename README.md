# Inventory API

REST API to manage the inventory of a small store: products, categories, suppliers and stock movements, with role-based permissions and aggregated reports.

Built with **Django**, **Django REST Framework** and **PostgreSQL**.

## Features

- Products, categories and suppliers (CRUD)
- **Stock movements** (in/out) as an immutable audit log
- **Database transactions with row locking** so stock can never go negative, even with concurrent requests
- **Roles**: admins (`is_staff`) manage the catalog; employees read and register movements
- Search, ordering, filters (`category`, `supplier`, `low_stock`, `is_active`) and pagination
- **Inventory report** computed with SQL aggregations: total units, stock value, low-stock products, totals per category
- Token authentication, Django admin panel
- Tests with pytest-django; CI runs them against PostgreSQL

## Tech stack

Python 3.12 · Django 5 · Django REST Framework · PostgreSQL 16 · pytest-django · Docker · GitHub Actions

## Data model

```
Category 1───* Product *───1 Supplier
                  │
                  1
                  │
                  * StockMovement *───1 User
```

## Getting started

### Docker

```bash
docker compose up --build
docker compose exec api python manage.py createsuperuser   # admin user
```

### Local (SQLite)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- API root: http://localhost:8000/api/
- Admin panel: http://localhost:8000/admin/

## Running tests

```bash
pytest --cov=inventory
ruff check .
```

## Endpoints

| Method | Endpoint | Who | Description |
|---|---|---|---|
| POST | `/api/auth/token/` | Anyone | Get a token (`username`, `password`) |
| GET/POST | `/api/categories/` | Read: all · Write: admin | Categories |
| GET/POST | `/api/suppliers/` | Read: all · Write: admin | Suppliers |
| GET/POST | `/api/products/` | Read: all · Write: admin | Products (`?search=`, `?low_stock=true`, `?category=`, `?ordering=-price`) |
| GET/PUT/PATCH/DELETE | `/api/products/{id}/` | Read: all · Write: admin | Product detail |
| GET/POST | `/api/movements/` | All users | List or register stock movements (`?product=`, `?type=in`) |
| GET | `/api/reports/summary/` | All users | Inventory report |
| GET | `/health/` | Anyone | Health check |

Send the token in the header: `Authorization: Token <your-token>`.

### Example

```bash
curl -X POST http://localhost:8000/api/movements/ \
  -H "Authorization: Token <TOKEN>" -H "Content-Type: application/json" \
  -d '{"product": 1, "movement_type": "OUT", "quantity": 3, "note": "Sale #120"}'
```

## Design decisions

- **Stock is read-only on the product.** It only changes through `StockMovement`, so every change is traceable (who, when, why).
- **`transaction.atomic` + `select_for_update()`** in `services.py`: the movement and the stock update succeed or fail together, and concurrent sales can't oversell.
- **Business logic lives in a service function**, not in the view, so it's easy to test and reuse.
- **`select_related`** avoids the N+1 query problem when listing products.
- **`on_delete=PROTECT`** on categories: deleting a category with products returns `409 Conflict`.
