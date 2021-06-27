from cassandra.cqlengine.models import Model
from cassandra.cqlengine.columns import Text, UUID, DateTime
from uuid import uuid4


class Item(Model):
    id = UUID(primary_key=True, default=uuid4)
    date_created = DateTime(primary_key=True)
    title = Text(primary_key=True)
    description = Text(required=False)
    media_type = Text(required=False)
    href = Text(required=False)

    @classmethod
    def with_keyspace(cls, keyspace=None):
        cls.__keyspace__ = keyspace
        return cls
