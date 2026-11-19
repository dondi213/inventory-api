# Guía rápida: Inventory API (Proyecto 3)

## Correrlo

```bash
docker compose up --build
docker compose exec api python manage.py createsuperuser
```

Entra a http://localhost:8000/admin/ con ese usuario y crea un segundo usuario **sin** "Staff status": ese será tu "empleado" para probar permisos.
DRF trae una interfaz web: abre http://localhost:8000/api/ e inicia sesión desde ahí (o usa el token).

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Qué debes poder explicar en una entrevista

- **Transacciones:** ¿qué pasaría sin `transaction.atomic` si falla el `create` del movimiento después de modificar el stock?
- **Concurrencia:** ¿qué problema resuelve `select_for_update()` cuando dos vendedores venden el último producto al mismo tiempo?
- **ORM:** diferencia entre `select_related` y `prefetch_related`; qué es el problema N+1.
- **Agregaciones:** cómo `Sum`, `Count` y `F()` calculan el reporte en la base de datos y no en Python.
- **Permisos:** cómo funciona `IsAdminOrReadOnly` y por qué los movimientos no se pueden editar ni borrar.
- **Migraciones:** qué hace `makemigrations` vs `migrate`.

## Retos para hacerlo tuyo

1. **Fácil:** endpoint `GET /api/products/{id}/movements/` con `@action`.
2. **Fácil:** filtro de movimientos por rango de fechas (`?from=2026-01-01&to=2026-01-31`).
3. **Medio:** documentación OpenAPI/Swagger con `drf-spectacular`.
4. **Medio:** exportar el reporte a CSV.
5. **Avanzado:** test de concurrencia con dos hilos vendiendo el último producto.
