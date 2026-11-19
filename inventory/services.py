from django.db import transaction
from rest_framework.exceptions import ValidationError

from inventory.models import Product, StockMovement


@transaction.atomic
def register_movement(
    *, product_id: int, movement_type: str, quantity: int, user, note: str = ""
) -> StockMovement:
    """Create a stock movement and update the product stock in ONE transaction.

    select_for_update() locks the product row, so two simultaneous "OUT" movements
    can't both read the same stock and leave it negative.
    """
    product = Product.objects.select_for_update().get(pk=product_id)

    if movement_type == StockMovement.MovementType.OUT:
        if quantity > product.stock:
            msg = f"Insufficient stock: available {product.stock}, requested {quantity}."
            raise ValidationError({"quantity": msg})
        product.stock -= quantity
    else:
        product.stock += quantity

    product.save(update_fields=["stock", "updated_at"])
    return StockMovement.objects.create(
        product=product,
        movement_type=movement_type,
        quantity=quantity,
        note=note,
        created_by=user,
    )
