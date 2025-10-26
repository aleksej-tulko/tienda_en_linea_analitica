import logging
import sys
import uuid

from confluent_kafka import avro, KafkaException, Producer
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema

BOOTSTRAP_SERVERS = (
    '100.110.19.157:19093,100.110.19.157:29093,100.110.19.157:39093'
)
PRODUCER_USERNAME = 'producer'
PRODUCER_PASSWORD = 'producer_pass'
SECURITY_PROTOCOL = 'SASL_SSL'
AUTH_MECHANISM = 'PLAIN'
SCHEMA_REGISTRY_URL = 'https://100.110.19.157:8081'
CACERT_PATH = 'client.p12'
TOPIC = 'mirroring'
SUBJECT = TOPIC + '-value'
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

schema_registry_client = SchemaRegistryClient(
    {
        'url': f'https://{SCHEMA_REGISTRY_URL}',
        'ssl.ca.location': CACERT_PATH,
    }
)

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


base_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'security.protocol': SECURITY_PROTOCOL,
    'sasl.mechanism': AUTH_MECHANISM,
    'ssl.ca.location': CACERT_PATH,
}
base_producer_conf = base_conf | {
    'sasl.username': PRODUCER_USERNAME,
    'sasl.password': PRODUCER_PASSWORD,
    'on_delivery': delivery_report,
}
avro_producer_conf = base_producer_conf | {
    'schema.registry.url': SCHEMA_REGISTRY_URL,
    'schema.registry.ssl.ca.location': CACERT_PATH,
}
avro_producer = avro.AvroProducer(
    avro_producer_conf,
    default_key_schema=key_schema,
    default_value_schema=value_schema,
)


def create_message(producer: avro.AvroProducer) -> None:
    """Отправка сообщения в брокер."""
    producer.produce(topic=TOPIC, key=key, value=value)


def producer_infinite_loop(producer: avro.AvroProducer) -> None:
    """Запуска цикла для генерации сообщения."""
    try:
        while True:
            create_message(producer=avro_producer)
            producer.flush()
    except (KafkaException, Exception):
        raise
    finally:
        producer.flush()


def register_schema_version():
    """Поиск зарегистрированной схемы или регистрация новой."""
    try:
        latest = schema_registry_client.get_latest_version(SUBJECT)
        logger.info(msg=LoggerMsg.SCHEMA_ALREADY_EXISTS.format(
            subject=SUBJECT, subject_str=latest.schema.schema_str
        ))
    except Exception:
        schema_object = Schema(VALUE_SCHEMA_STR, 'AVRO')
        schema_id = schema_registry_client.register_schema(
            SUBJECT, schema_object
        )
        logger.info(msg=LoggerMsg.SCHEMA_REGISTERED.format(
            subject=SUBJECT, schema_id=schema_id
        ))


if __name__ == '__main__':
    """Запуск программы."""
    register_schema_version()