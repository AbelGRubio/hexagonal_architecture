"""Auto-generated Peewee model."""

from peewee import CharField, DateTimeField, Model

from event_driven.infrastructure.persistence.connection import get_database


class OrderCreated(Model):
    """Order creation."""

    event_id = CharField(default="xxx555", null=True)

    items = CharField(default=[], null=True)

    order_id = CharField(default="xxx999", null=True)

    timestamp = DateTimeField(null=True)

    user_id = CharField(null=True)

    class Meta:
        """Class meta."""

        database = get_database()
        table_name = "order_created"
