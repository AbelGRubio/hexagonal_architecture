"""Auto-generated Peewee model."""

from peewee import CharField, FloatField, IntegerField, Model

from event_driven.infrastructure.persistence.connection import get_database


class Cartitem(Model):
    """Cart item."""

    name = CharField(null=True)

    product_id = CharField(default="xxxx7", null=True)

    quantity = IntegerField(default=0, null=True)

    unit_price = FloatField(default=0, null=True)

    class Meta:
        """Class meta."""

        database = get_database()
        table_name = "cart_item"
