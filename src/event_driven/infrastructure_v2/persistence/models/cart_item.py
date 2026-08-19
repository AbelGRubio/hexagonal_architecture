"""Auto-generated Peewee model."""

from peewee import CharField, FloatField, IntegerField, Model

from event_driven.infrastructure.persistence.connection import get_database


class Cartitem(Model):
    """Cart item."""

    product_id = CharField(null=True, default="xxxxxx")

    name = CharField(null=True)

    quantity = IntegerField(null=True, default=0)

    unit_price = FloatField(null=True, default=0)

    class Meta:
        """Class meta."""

        database = get_database()
        table_name = "cart_item"
