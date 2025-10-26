import json
import logging
import os
import ssl
import sys
import uuid
from threading import Thread
from time import sleep

from confluent_kafka import avro, KafkaException, Producer
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from dotenv import load_dotenv


load_dotenv()

BOOTSTRAP_SERVERS = os.getenv('BOOTSTRAP_SERVERS', 'localhost:9092')
PRODUCER_USERNAME = os.getenv('PRODUCER_USERNAME', 'producer')
PRODUCER_PASSWORD = os.getenv('PRODUCER_PASSWORD', '')
SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://localost:8081')
CA_PATH = os.getenv('CA_PATH', './client_fullchain.pem')
CERT_PATH = os.getenv('CERT_PATH', './client.crt')
CERT_KEY_PATH = os.getenv('CERT_KEY_PATH', './client.key')
DLQ = os.getenv('DLQ', 'topic')
ACKS_LEVEL = os.getenv('ACKS_LEVEL', 'all')
RETRIES = os.getenv('RETRIES', '3')
LINGER_MS = os.getenv('LINGER_MS', 5)
COMPRESSION_TYPE = os.getenv('COMPRESSION_TYPE', 'lz4')
PRODUCER_USERNAME = os.getenv('PRODUCER_USERNAME', 'producer')
SHOP_UNSORTED_TOPIC = os.getenv('SHOP_UNSORTED_TOPIC', 'topic')
SUBJECT = SHOP_UNSORTED_TOPIC + 'unsorted'
SECURITY_PROTOCOL = 'SASL_SSL'
AUTH_MECHANISM = 'PLAIN'
KEY_SCHEMA_STR = """
{
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
"""
VALUE_SCHEMA_STR = """
{
    "namespace": "product_item",
    "name": "value",
    "type": "record",
    "fields": [
        {
            "name": "name",
            "type": "string"
        },
        {
            "name": "info",
            "type": "string"
        }
    ]
}
"""

key_schema = avro.loads(KEY_SCHEMA_STR)
value_schema = avro.loads(VALUE_SCHEMA_STR)
key = {'name': f'key-{uuid.uuid4()}'}
value = {'name': f'val-{uuid.uuid4()}', 'info': f'info-{uuid.uuid4()}'}

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
    MSG_DELIVERED = 'Сообщение доставлено в {topic} в раздел {partition}.'
    MSG_RECEIVED = 'Сообщение получено: {value}.'
    MSG_NOT_DESERIALIZED = 'Сообщение не десериализовано:'
    SCHEMA_ALREADY_EXISTS = ('Схема уже зарегистрирована '
                             'для {subject}: \n{subject_str}.')
    SCHEMA_REGISTERED = ('Зарегистрирована схема {subject} '
                         'с ID {schema_id}.')
    PROGRAM_RUNNING = 'Выполняется программа.'


def delivery_report(err, msg) -> None:
    """Отчет о доставке."""
    if err is not None:
        logger.error(msg=LoggerMsg.MSG_NOT_DELIVERED.format(err=err))
    else:
        logger.info(
            msg=LoggerMsg.MSG_DELIVERED.format(
                topic=msg.topic(),
                partition=msg.partition()
            )
        )


conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'security.protocol': SECURITY_PROTOCOL,
    'sasl.mechanism': AUTH_MECHANISM,
    'ssl.ca.location': CA_PATH,
    'sasl.username': PRODUCER_USERNAME,
    'sasl.password': PRODUCER_PASSWORD,
    'schema.registry.url': SCHEMA_REGISTRY_URL,
    'schema.registry.ssl.ca.location': CA_PATH,
    'schema.registry.ssl.certificate.location': CERT_PATH,
    'schema.registry.ssl.key.location': CERT_KEY_PATH,
    'on_delivery': delivery_report,
}
producer = avro.AvroProducer(
    config=conf,
    default_key_schema=key_schema,
    default_value_schema=value_schema,
)

ca_ctx = ssl.create_default_context()
ca_ctx.load_verify_locations(cafile=CA_PATH)
schema_registry_client = SchemaRegistryClient(
    {
        'url': SCHEMA_REGISTRY_URL,
        'ssl.ca.location': ca_ctx,
        'ssl.certificate.location': CERT_PATH,
        'ssl.key.location': CERT_KEY_PATH,
    }
)


def create_message(producer: avro.AvroProducer) -> None:
    """Отправка сообщения в брокер."""
    producer.produce(topic=SHOP_UNSORTED_TOPIC, key=key, value=value)


def producer_infinite_loop(producer: avro.AvroProducer) -> None:
    """Запуска цикла для генерации сообщения."""
    try:
        while True:
            create_message(producer=producer)
            producer.flush()
    except (KafkaException, Exception):
        raise
    finally:
        producer.flush()


def send_to_dlq(dlq_producer, key, value, error) -> None:
    """Отправка сообщений в Dead Letter Queue."""
    payload = {
        'key': key,
        'value': value,
        'error': str(error),
    }
    dlq_producer.produce(
        topic=DLQ,
        key=str(key).encode(),
        value=json.dumps(payload).encode('utf-8'),
    )
    dlq_producer.flush()


def register_schema_version():
    """Поиск зарегистрированной схемы или регистрация новой."""
    try:
        latest = schema_registry_client.get_latest_version(SUBJECT)
        logger.info(
            msg=LoggerMsg.SCHEMA_ALREADY_EXISTS.format(
                subject=SUBJECT, subject_str=latest.schema.schema_str
            )
        )
    except Exception:
        schema_object = Schema(VALUE_SCHEMA_STR, 'AVRO')
        schema_id = schema_registry_client.register_schema(
            SUBJECT, schema_object
        )
        logger.info(
            msg=LoggerMsg.SCHEMA_REGISTERED.format(
                subject=SUBJECT, schema_id=schema_id
            )
        )


if __name__ == '__main__':
    """Запуск программы."""
    register_schema_version()

    producer_thread = Thread(
        target=producer_infinite_loop,
        args=(producer,),
        daemon=True
    )

    producer_thread.start()

    while True:
        logger.debug(msg=LoggerMsg.PROGRAM_RUNNING)
        sleep(10)
