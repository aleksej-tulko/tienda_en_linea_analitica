import faust
from schema_registry.serializers.faust import FaustSerializer


class ProhibitedProducts(faust.Record):
    """Модель запрещенных товаров."""

    goods: list[str]


app = faust.App(
    "goods_filter",
    broker="kafka://localhost:19093,localhost:29093,localhost:39093",
    store="rocksdb://",
)

goods_topic = app.topic(
    'raw_items',
    key_type=str,
    value_type=str,
    key_serializer=FaustSerializer
)