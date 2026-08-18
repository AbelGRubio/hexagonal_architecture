"""Auto-generated Peewee model."""

from event_driven.models.db_models import get_database
from peewee import CharField, Model


class Ordercreated(Model):
    """Order creation."""

    event_id = CharField(null=True, default=888888)

    order_id = CharField(null=True, default=9999999)

    user_id = CharField(null=True)

    items = CharField(null=True, default=[])

    timestamp = CharField(null=True, default="timestamp.now")

    class Meta:
        """Class meta."""

        database = get_database()
        table_name = "order_created"
