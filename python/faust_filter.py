import logging
import os
import ssl
import sys

import faust
from dotenv import load_dotenv
from faust_avro_serializer import FaustAvroSerializer
from schema_registry.client import SchemaRegistryClient

load_dotenv()

BOOTSTRAP_SERVERS = (
    'kafka://' + os.getenv('BOOTSTRAP_SERVERS', 'localhost:9093')
)
SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://localost:8081')
CA_PATH = os.getenv('CA_PATH', './client_fullchain.pem')
CERT_PATH = os.getenv('CERT_PATH', './client.crt')
CERT_KEY_PATH = os.getenv('CERT_KEY_PATH', './client.key')
SHOP_UNSORTED_TOPIC = os.getenv('SHOP_UNSORTED_TOPIC', 'topic')
SHOP_SORTED_TOPIC = os.getenv('SHOP_SORTED_TOPIC', 'topic')
SHOP_BLOCKED_GOODS_TOPIC = os.getenv('SHOP_BLOCKED_GOODS_TOPIC', 'topic')
PRODUCER_USERNAME = os.getenv('PRODUCER_USERNAME', 'producer')
PRODUCER_PASSWORD = os.getenv('PRODUCER_PASSWORD', '')
APP_NAME = 'goods_filter'
FILTER_TABLE = 'filter_anchors'

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class LoggerMsg:
    """Сообщения для логгирования."""

    PRICE_EQUALS = 'Цена {item}: {price}.'
    GOODS_PROHIBITED = 'Запрещенные товары: {goods}.'


class FilterWords(faust.Record):
    """Модель для слов-якорей для фильтра."""

    words: list[str]


class ProhibitedProducts(faust.Record):
    """Модель запрещенных товаров."""

    item: list[str]


class Price(faust.Record):
    """Модель цены."""

    amount: float
    currency: str


class Stock(faust.Record):
    """Модель стока."""

    available: int
    reserved: int


class Image(faust.Record):
    """Модель фото."""

    url: str
    alt: str


class Specifications(faust.Record):
    """Модель тех. характеристик."""

    weight: str
    dimensions: str
    battery_life: str
    water_resistance: str


class SchemaKey(faust.Record):
    _schema = {
        "namespace": "product_id",
        "name": "key",
        "type": "record",
        "fields": [
            {
                "name": "name",
                "type": "string"
            }
        ]
    }
    name: str


class SchemaValue(faust.Record):
    _schema = {
        "namespace": "product_item",
        "name": "product",
        "type": "record",
        "fields": [
            {"name": "product_id", "type": "string"},
            {"name": "name", "type": "string"},
            {"name": "description", "type": "string"},
            {
                "name": "price",
                "type": {
                    "type": "record",
                    "name": "Price",
                    "fields": [
                        {"name": "amount", "type": "double"},
                        {"name": "currency", "type": "string"}
                    ]
                }
            },
            {"name": "category", "type": "string"},
            {"name": "brand", "type": "string"},
            {
                "name": "stock",
                "type": {
                    "type": "record",
                    "name": "Stock",
                    "fields": [
                        {"name": "available", "type": "int"},
                        {"name": "reserved", "type": "int"}
                    ]
                }
            },
            {"name": "sku", "type": "string"},
            {"name": "tags", "type": {"type": "array", "items": "string"}},
            {
                "name": "images",
                "type": {
                    "type": "array",
                    "items": {
                        "type": "record",
                        "name": "Image",
                        "fields": [
                            {"name": "url", "type": "string"},
                            {"name": "alt", "type": "string"}
                        ]
                    }
                }
            },
            {
                "name": "specifications",
                "type": {
                    "type": "record",
                    "name": "Specifications",
                    "fields": [
                        {"name": "weight", "type": "string"},
                        {"name": "dimensions", "type": "string"},
                        {"name": "battery_life", "type": "string"},
                        {"name": "water_resistance", "type": "string"}
                    ]
                }
            },
            {"name": "created_at", "type": "string"},
            {"name": "updated_at", "type": "string"},
            {"name": "index", "type": "string"},
            {"name": "store_id", "type": "string"}
        ]
    }
    product_id: str
    name: str
    description: str
    price: Price
    category: str
    brand: str
    stock: Stock
    sku: str
    tags: list[str]
    images: list[Image]
    specifications: Specifications
    created_at: str
    updated_at: str
    index: str
    store_id: str


ca_ctx = ssl.create_default_context()
ca_ctx.load_verify_locations(cafile=CA_PATH)
ca_ctx.load_cert_chain(certfile=CERT_PATH, keyfile=CERT_KEY_PATH)

schema_registry_client = SchemaRegistryClient(
    {
        'url': SCHEMA_REGISTRY_URL,
        'ssl.ca.location': ca_ctx,
        'ssl.certificate.location': CERT_PATH,
        'ssl.key.location': CERT_KEY_PATH,
    }
)
serializer = FaustAvroSerializer(
    schema_registry_client, SHOP_UNSORTED_TOPIC, False
)
schema_with_avro = faust.Schema(
    key_type=SchemaKey,
    value_type=SchemaValue,
    key_serializer=serializer,
    value_serializer=serializer)

app = faust.App(
    APP_NAME,
    broker=BOOTSTRAP_SERVERS,
    broker_credentials=faust.SASLCredentials(
        username=PRODUCER_USERNAME,
        password=PRODUCER_PASSWORD,
        ssl_context=ca_ctx
    ),
    store='rocksdb://',
)

filter_table = app.Table(
    FILTER_TABLE,
    partitions=1,
    default=list,
    changelog_topic=app.topic(
        'filter-table-changelog',
        value_type=ProhibitedProducts(item=list[str]),
        partitions=1
    )
)

app.conf.consumer_auto_offset_reset = 'earliest'

goods_topic = app.topic(SHOP_UNSORTED_TOPIC, schema=schema_with_avro)
sorted_goods_topic = app.topic(SHOP_SORTED_TOPIC, schema=schema_with_avro)
prohibited_goods_topic = app.topic(
    SHOP_BLOCKED_GOODS_TOPIC,
    key_type=str,
    value_type=ProhibitedProducts,
    acks='all'
)


def log_prohibited_items(data: tuple) -> None:
    logger.info(
        msg=LoggerMsg.GOODS_PROHIBITED.format(
            goods=data
        )
    )


def log_price(data: tuple) -> None:
    name, price = data
    logger.info(
        msg=LoggerMsg.PRICE_EQUALS.format(
            item=name, price=price
        )
    )


def convert_price(value: SchemaValue) -> SchemaValue:
    try:
        value.price.amount = float(value.price.amount)
    except TypeError as TE:
        raise f'Cannot convert price to float value {TE}'
    return value


@app.agent(prohibited_goods_topic, sink=[log_prohibited_items])
async def filter_prohibited_goods(stream):
    async for good in stream.group_by(key='item'):
        current = filter_table['prohibited']
        updated = [*current, *good.item]
        filter_table['prohibited'] = updated
        yield tuple(updated)


@app.agent(goods_topic, sink=[log_price])
async def add_filtered_record(stream):
    processed_stream = app.stream(
        stream,
        processors=[convert_price]
    )
    async for record in processed_stream:
        print(filter_table['prohibited'])
        if record.name in filter_table['prohibited']:
            continue
        await sorted_goods_topic.send(
            value=record
        )
        yield (record.name, record.price.amount)
