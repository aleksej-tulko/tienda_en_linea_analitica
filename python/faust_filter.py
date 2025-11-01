import os
import ssl
import faust
from faust_avro_serializer import FaustAvroSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient

# Загрузи из .env
CA_PATH = os.getenv("CA_PATH")
CERT_PATH = os.getenv("CERT_PATH")
CERT_KEY_PATH = os.getenv("CERT_KEY_PATH")
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL", "http://localhost:8081")
BROKER_URL = os.getenv("BOOTSTRAP_SERVERS", "kafka://localhost:9092")
PRODUCER_USERNAME = os.getenv("PRODUCER_USERNAME")
PRODUCER_PASSWORD = os.getenv("PRODUCER_PASSWORD")
SHOP_UNSORTED_TOPIC = os.getenv("SHOP_UNSORTED_TOPIC", "raw_items")
SHOP_SORTED_TOPIC = os.getenv("SHOP_SORTED_TOPIC", "sorted_items")

# SSL-контекст (используй только если все пути заданы)
ca_ctx = ssl.create_default_context()
if CA_PATH and os.path.exists(CA_PATH):
    ca_ctx.load_verify_locations(cafile=CA_PATH)
if CERT_PATH and CERT_KEY_PATH and os.path.exists(CERT_PATH) and os.path.exists(CERT_KEY_PATH):
    ca_ctx.load_cert_chain(CERT_PATH, keyfile=CERT_KEY_PATH)

# Клиент SR: передаём пути, не контекст
schema_registry_client = SchemaRegistryClient({
    "url": SCHEMA_REGISTRY_URL,
    **({"ssl.ca.location": CA_PATH} if CA_PATH else {}),
    **({"ssl.certificate.location": CERT_PATH} if CERT_PATH else {}),
    **({"ssl.key.location": CERT_KEY_PATH} if CERT_KEY_PATH else {}),
})

# Дальше всё как раньше
in_ser  = FaustAvroSerializer(schema_registry_client, SHOP_UNSORTED_TOPIC, False)
out_ser = FaustAvroSerializer(schema_registry_client, SHOP_SORTED_TOPIC,  False)