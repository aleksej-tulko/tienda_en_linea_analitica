import logging
import os
import re
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


class Product(faust.Record):

    id: int
    name: str
    amount: int
    price: float


class LoggerMsg:

    DATE_SPENT = 'On {ingressed_at} spent total is {total_spent}.'
    BRANDS_PROHIBITED = 'Prohibited brands: {brands}.'


class ProhibitedBrands(faust.Record):

    brands: list[str]


class SchemaKey(faust.Record):
    _schema = {
        "namespace": "key",
        "name": "date",
        "type": "record",
        "fields": [
            {
                "name": "date",
                "type": "string"
            }
        ]
    }
    date: str


class SchemaValue(faust.Record, serializer='json'):
    _schema = {
        "namespace": "value",
        "name": "product_details",
        "type": "record",
        "fields": [
            {"name": "id", "type": "int"},
            {
                "name": "products",
                "type": {
                    "type": "array",
                        "items": {
                            "type": "record",
                            "name": "product",
                            "fields": [
                                {"name": "id", "type": "int"},
                                {"name": "name", "type": "string"},
                                {"name": "amount", "type": "int"},
                                {"name": "price", "type": "double"}
                            ]
                        }
                }
            },
            {"name": "description", "type": "string"},
            {"name": "category", "type": "string"},
            {"name": "brand", "type": "string"},
            {"name": "tags", "type": {"type": "array", "items": "string"}},
            {"name": "compra_total", "type": "double"},
            {"name": "ingressed_at", "type": "string"}
        ]
    }
    id: int
    products: list[Product]
    description: str
    category: str
    brand: str
    tags: list[str]
    compra_total: float
    ingressed_at: str


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
    default=ProhibitedBrands(brands=list[str]),
    changelog_topic=app.topic(
        FILTER_TABLE_CHANGELOG_TOPIC,
        value_type=ProhibitedBrands(brands=list[str]),
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
    value_type=str,
    acks=True
)

prohibited_goods_topic = app.topic(
    SHOP_BLOCKED_GOODS_TOPIC,
    key_type=str,
    value_type=ProhibitedBrands,
    acks=True
)


def log_prohibited_products(brands: ProhibitedBrands) -> None:
    logger.info(
        msg=LoggerMsg.BRANDS_PROHIBITED.format(
            brands=brands.brands
        )
    )


def log_spent(data: tuple) -> None:
    ingressed_at, total_spent = data
    logger.info(
        msg=LoggerMsg.DATE_SPENT.format(
            ingressed_at=ingressed_at, total_spent=total_spent
        )
    )


@app.agent(prohibited_goods_topic, sink=[log_prohibited_products])
async def filter_prohibited_products(prohibited_brands):
    async for brand in prohibited_brands:
        filter_table['prohibited'] = ProhibitedBrands(
            brands=brand.brands
        )
        yield filter_table['prohibited']


@app.agent(goods_topic, sink=[log_spent])
async def add_filtered_record(products):
    processed_products = app.stream(products)
    async for product in processed_products:
        if not re.match(re_pattern, product.category):
            continue
        if 'prohibited' in filter_table:
            if product.brand in filter_table['prohibited'].brands:
                continue
        await sorted_goods_topic.send(
            key=product.ingressed_at + str(product.compra_total),
            value=product.asdict()
        )
        yield (product.ingressed_at, product.compra_total)
