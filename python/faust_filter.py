import faust
import ssl
from faust_avro_serializer import FaustAvroSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient

# === конфиг ===
BOOTSTRAP = "kafka://100.110.19.157:19093,100.110.19.157:29093,100.110.19.157:39093"
SHOP_UNSORTED_TOPIC = "raw_items"          # твой топик из логов
SHOP_SORTED_TOPIC   = "sorted_items"        # другой топик для вывода
SCHEMA_REGISTRY_URL = "http://localhost:8081"  # БЕЗ опечатки

CA_PATH = "./client_fullchain.pem"
CERT_PATH = "./client.crt"
CERT_KEY_PATH = "./client.key"
PRODUCER_USERNAME = "producer"
PRODUCER_PASSWORD = "..."

# === SSL для брокера (не для SR) ===
ca_ctx = ssl.create_default_context()
ca_ctx.load_verify_locations(cafile=CA_PATH)
ca_ctx.load_cert_chain(CERT_PATH, keyfile=CERT_KEY_PATH)

# === SR-клиент: ВАЖНО — пути, НЕ SSLContext ===
sr_client = SchemaRegistryClient({
    "url": SCHEMA_REGISTRY_URL,
    "ssl.ca.location": CA_PATH,
    "ssl.certificate.location": CERT_PATH,
    "ssl.key.location": CERT_KEY_PATH,
})

# === сериалайзеры Confluent Avro для key и value ===
in_key_ser   = FaustAvroSerializer(sr_client, SHOP_UNSORTED_TOPIC, True)   # is_key=True
in_value_ser = FaustAvroSerializer(sr_client, SHOP_UNSORTED_TOPIC, False)  # is_key=False
out_key_ser  = FaustAvroSerializer(sr_client, SHOP_SORTED_TOPIC,   True)
out_val_ser  = FaustAvroSerializer(sr_client, SHOP_SORTED_TOPIC,   False)

# === модели (как у тебя) ===
class SchemaKey(faust.Record):
    name: str

class Price(faust.Record):
    amount: float
    currency: str

class Stock(faust.Record):
    available: int
    reserved: int

class Image(faust.Record):
    url: str
    alt: str

class Specifications(faust.Record):
    weight: str
    dimensions: str
    battery_life: str
    water_resistance: str

class SchemaValue(faust.Record):
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

# === Faust app ===
app = faust.App(
    "goods_filter",
    broker=BOOTSTRAP,
    broker_credentials=faust.SASLCredentials(
        username=PRODUCER_USERNAME,
        password=PRODUCER_PASSWORD,
        ssl_context=ca_ctx,
        mechanism="PLAIN",
    ),
    consumer_auto_offset_reset="earliest",   # чтобы увидеть старые сообщения
)

# === правильные схемы топиков ===
in_schema = faust.Schema(
    key_type=SchemaKey, value_type=SchemaValue,
    key_serializer=in_key_ser, value_serializer=in_value_ser,
)
out_schema = faust.Schema(
    key_type=SchemaKey, value_type=SchemaValue,
    key_serializer=out_key_ser, value_serializer=out_val_ser,
)

goods_topic = app.topic(SHOP_UNSORTED_TOPIC, schema=in_schema)
sorted_goods_topic = app.topic(SHOP_SORTED_TOPIC,  schema=out_schema)

# — полезно видеть назначение партиций
@app.on_partitions_assigned
async def _assigned(sender, partitions, **kw):
    app.log.info("ASSIGNED: %s", sorted(list(partitions)))

# === агент с логом событий (ключ, оффсет) ===
@app.agent(goods_topic)
async def my_agent(stream: faust.Stream[SchemaValue]):
    async for event in stream.events():
        app.log.info("IN tp=%s/%s off=%s key=%r",
                     event.message.topic, event.message.partition, event.message.offset,
                     event.key)
        app.log.info("VALUE: %r", event.value)   # <- тут появится твой record
        await sorted_goods_topic.send(value=event.value, key=event.key)