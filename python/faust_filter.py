import os
import ssl
import faust
from faust_avro_serializer import FaustAvroSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from dotenv import load_dotenv


load_dotenv()


# === ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
CA_PATH = os.getenv("CA_PATH")
CERT_PATH = os.getenv("CERT_PATH")
CERT_KEY_PATH = os.getenv("CERT_KEY_PATH")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
BROKER_URL = os.getenv("BOOTSTRAP_SERVERS", "kafka://localhost:9092")
PRODUCER_USERNAME = os.getenv("PRODUCER_USERNAME", "")
PRODUCER_PASSWORD = os.getenv("PRODUCER_PASSWORD", "")
SHOP_UNSORTED_TOPIC = os.getenv("SHOP_UNSORTED_TOPIC", "raw_items")
SHOP_SORTED_TOPIC = os.getenv("SHOP_SORTED_TOPIC", "sorted_items")


# === SSL-КОНТЕКСТ ДЛЯ KAFKA (если нужны сертификаты) ===
ca_ctx = ssl.create_default_context()
if CA_PATH and os.path.exists(CA_PATH):
    ca_ctx.load_verify_locations(cafile=CA_PATH)
if CERT_PATH and CERT_KEY_PATH and os.path.exists(CERT_PATH) and os.path.exists(CERT_KEY_PATH):
    ca_ctx.load_cert_chain(CERT_PATH, keyfile=CERT_KEY_PATH)


# === SCHEMA REGISTRY CLIENT ===
schema_registry_client = SchemaRegistryClient({
    "url": SCHEMA_REGISTRY_URL,
    **({"ssl.ca.location": CA_PATH} if CA_PATH else {}),
    **({"ssl.certificate.location": CERT_PATH} if CERT_PATH else {}),
    **({"ssl.key.location": CERT_KEY_PATH} if CERT_KEY_PATH else {}),
})


# === СЕРИАЛАЙЗЕРЫ ===
in_ser = FaustAvroSerializer(schema_registry_client, SHOP_UNSORTED_TOPIC, False)
out_ser = FaustAvroSerializer(schema_registry_client, SHOP_SORTED_TOPIC, False)


# === FAUST APP ===
app = faust.App(
    "goods_filter",
    broker=BROKER_URL,
    broker_credentials=faust.SASLCredentials(
        username=PRODUCER_USERNAME,
        password=PRODUCER_PASSWORD,
        ssl_context=ca_ctx,
        mechanism="PLAIN",
    ),
    consumer_auto_offset_reset="earliest",
)


# === МОДЕЛИ ===
class Price(faust.Record):
    amount: float
    currency: str


class SchemaValue(faust.Record):
    product_id: str
    name: str
    description: str
    price: Price
    category: str
    brand: str
    created_at: str
    updated_at: str


# === ТОПИКИ ===
in_schema = faust.Schema(value_serializer=in_ser, value_type=SchemaValue)
out_schema = faust.Schema(value_serializer=out_ser, value_type=SchemaValue)

goods_topic = app.topic(SHOP_UNSORTED_TOPIC, schema=in_schema)
sorted_goods_topic = app.topic(SHOP_SORTED_TOPIC, schema=out_schema)


# === АГЕНТ ===
@app.agent(goods_topic)
async def my_agent(stream: faust.Stream[SchemaValue]):
    async for event in stream.events():
        app.log.info("Получено сообщение: %r", event.value)
        await sorted_goods_topic.send(value=event.value)