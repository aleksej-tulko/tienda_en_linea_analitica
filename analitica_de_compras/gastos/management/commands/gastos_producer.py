import logging
import ssl
import sys
from datetime import datetime

from confluent_kafka import avro
from confluent_kafka.schema_registry import SchemaRegistryClient
from django.conf import settings
from dotenv import load_dotenv


load_dotenv()

SECURITY_PROTOCOL = 'SASL_SSL'
AUTH_MECHANISM = 'PLAIN'
KEY_SCHEMA_STR = """
{
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
"""
VALUE_SCHEMA_STR = """
{
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
"""

key_schema = avro.loads(KEY_SCHEMA_STR)
value_schema = avro.loads(VALUE_SCHEMA_STR)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class LoggerMsg:
    """Сообщения для логгирования."""

    MSG_NOT_DELIVERED = 'Ошибка доставки {err}.'
    MSG_DELIVERED = (
        'Сообщение доставлено в {topic} '
        'в раздел {partition} с ключом {key}.'
    )
    PROGRAM_RUNNING = 'Выполняется программа.'


def delivery_report(err, msg) -> None:
    """Отчет о доставке."""
    if err is not None:
        logger.error(msg=LoggerMsg.MSG_NOT_DELIVERED.format(err=err))
    else:
        logger.info(
            msg=LoggerMsg.MSG_DELIVERED.format(
                topic=msg.topic(),
                key=msg.key(),
                partition=msg.partition()
            )
        )


conf = {
    'bootstrap.servers': settings.BOOTSTRAP_SERVERS,
    'security.protocol': SECURITY_PROTOCOL,
    'sasl.mechanism': AUTH_MECHANISM,
    'ssl.ca.location': settings.CA_PATH,
    'sasl.username': settings.PRODUCER_USERNAME,
    'sasl.password': settings.PRODUCER_PASSWORD,
    'schema.registry.url': settings.SCHEMA_REGISTRY_URL,
    'schema.registry.ssl.ca.location': settings.CA_PATH,
    'schema.registry.ssl.certificate.location': settings.CERT_PATH,
    'schema.registry.ssl.key.location': settings.CERT_KEY_PATH,
    'on_delivery': delivery_report,
}
producer = avro.AvroProducer(
    config=conf,
    default_key_schema=key_schema,
    default_value_schema=value_schema,
)

ca_ctx = ssl.create_default_context()
ca_ctx.load_verify_locations(cafile=settings.CA_PATH)
schema_registry_client = SchemaRegistryClient(
    {
        'url': settings.SCHEMA_REGISTRY_URL,
        'ssl.ca.location': ca_ctx,
        'ssl.certificate.location': settings.CERT_PATH,
        'ssl.key.location': settings.CERT_KEY_PATH,
    }
)


def produce_message(message: dict, producer: avro.AvroProducer = producer) -> None:
    """Отправка сообщения в брокер."""
    try:
        key = {'date': message['ingressed_at']}
        producer.produce(
            topic=settings.SHOP_UNSORTED_TOPIC,
            key=key,
            value=message,
            headers={'datetime': datetime.now().strftime('%Y-%m-%d %H:%M')}
        )
        producer.flush()
    except (Exception):
        raise
    finally:
        producer.flush()
