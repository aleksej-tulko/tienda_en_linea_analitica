import json
import logging
import os
import re
import ssl
import sys

import faust
from faust.serializers import codecs
from dotenv import load_dotenv
from faust_avro_serializer import FaustAvroSerializer
from schema_registry.client import SchemaRegistryClient

load_dotenv()

BOOTSTRAP_SERVERS = (
    'kafka://' + os.getenv('BOOTSTRAP_SERVERS', 'localhost:9093')
)
SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://localost:8081')
CA_PATH = os.getenv('CA_PATH')
CERT_PATH = os.getenv('CERT_PATH')
CERT_KEY_PATH = os.getenv('CERT_KEY_PATH')
SHOP_UNSORTED_TOPIC = os.getenv('SHOP_UNSORTED_TOPIC', 'topic')
SHOP_SORTED_TOPIC = os.getenv('SHOP_SORTED_TOPIC', 'topic')
SHOP_BLOCKED_GOODS_TOPIC = os.getenv('SHOP_BLOCKED_GOODS_TOPIC', 'topic')
PRODUCER_USERNAME = os.getenv('FAUST_USERNAME', 'faust')
PRODUCER_PASSWORD = os.getenv('FAUST_PASSWORD', '')
APP_NAME = 'goods_filter'
FILTER_TABLE = os.getenv('FILTER_TABLE', 'table')
FILTER_TABLE_CHANGELOG_TOPIC = os.getenv(
    'FILTER_TABLE_CHANGELOG_TOPIC', 'topic'
)

prohibited_goods_regexp = r'^[A-Za-zА-Яа-яЁё0-9 _-]+$'
re_pattern = re.compile(prohibited_goods_regexp, re.IGNORECASE)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class LoggerMsg:
    """Сообщения для логгирования."""

    PRICE_EQUALS = 'Цена {product}: {price}.'
    PRODUCTS_PROHIBITED = 'Запрещенные товары: {products}.'


class ProhibitedProducts(faust.Record):
    """Модель запрещенных товаров."""

    products: list[str]


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


class SchemaValue(faust.Record, serializer='json'):
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

key_serializer = FaustAvroSerializer(
    schema_registry_client, SHOP_UNSORTED_TOPIC, True
)

value_serializer = FaustAvroSerializer(
    schema_registry_client, SHOP_UNSORTED_TOPIC, False
)

schema_with_avro = faust.Schema(
    key_type=SchemaKey,
    value_type=SchemaValue,
    key_serializer=key_serializer,
    value_serializer=value_serializer)

app = faust.App(
    APP_NAME,
    broker=BOOTSTRAP_SERVERS,
    broker_credentials=faust.SASLCredentials(
        username=PRODUCER_USERNAME,
        password=PRODUCER_PASSWORD,
        ssl_context=ca_ctx
    ),
    # store='rocksdb://'
)

filter_table = app.Table(
    FILTER_TABLE,
    partitions=1,
    default=ProhibitedProducts(products=list[str]),
    changelog_topic=app.topic(
        FILTER_TABLE_CHANGELOG_TOPIC,
        value_type=ProhibitedProducts(products=list[str]),
        partitions=1,
        replicas=3
    )
)

app.conf.consumer_auto_offset_reset = 'earliest'

goods_topic = app.topic(
    SHOP_UNSORTED_TOPIC,
    schema=schema_with_avro,
    acks=True
)
sorted_goods_topic = app.topic(
    SHOP_SORTED_TOPIC,
    key_type=str,
    value_type=SchemaValue,
    acks=True
)

prohibited_goods_topic = app.topic(
    SHOP_BLOCKED_GOODS_TOPIC,
    key_type=str,
    value_type=ProhibitedProducts,
    acks=True
)


def log_prohibited_products(products: ProhibitedProducts) -> None:
    logger.info(
        msg=LoggerMsg.PRODUCTS_PROHIBITED.format(
            products=products
        )
    )


def log_price(product: tuple) -> None:
    name, price = product
    logger.info(
        msg=LoggerMsg.PRICE_EQUALS.format(
            product=name, price=price
        )
    )


def convert_price_to_float(value: SchemaValue) -> SchemaValue:
    try:
        value.price.amount = float(value.price.amount)
    except TypeError as TE:
        raise f'Cannot convert price to float value {TE}'
    return value


@app.agent(prohibited_goods_topic, sink=[log_prohibited_products])
async def filter_prohibited_products(prohibited_products):
    async for products in prohibited_products:
        filter_table['prohibited'] = ProhibitedProducts(
            products=products.products
        )
        yield filter_table['prohibited']


@app.agent(goods_topic, sink=[log_price])
async def add_filtered_record(products):
    processed_products = app.stream(
        products,
        processors=[convert_price_to_float]
    )
    async for product in processed_products:
        if not re.match(re_pattern, product.category):
            continue
        if 'prohibited' in filter_table:
            if product.name in filter_table['prohibited'].products:
                continue
        await sorted_goods_topic.send(
            key=product.name,
            value=product.dumps()
        )
        yield (product.name, product.price.amount)
