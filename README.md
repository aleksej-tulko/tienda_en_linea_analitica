# tienda_en_linea_analitica

# Подготовка рабочей среды

1. Склонировать репозиторий и перейти в него:
```bash
cd ~
git clone https://github.com/aleksej-tulko/tienda_en_linea_analitica.git
cd tienda_en_linea_analitica
```

2. Поднять Vault и подоготовить к работе:

```bash
sudo docker compose up vault -d
sudo docker compose exec vault vault operator init -key-shares=1 -key-threshold=1 > init.txt
sudo docker compose exec vault sh -c 'echo "changeit" > /vault/secrets/kafka_creds'
cat init.txt
sudo docker compose exec -it vault sh
vault operator unseal # Запросит ввести Unseal Key 1 из файла init.txt
export VAULT_TOKEN=XXXX # Подставить Initial Root Token из файла init.txt
```

3. Настроить Vault для создания корневого и промежуточных сертификатов. Cобрать truststore и keystore'ы для сервисов:

```bash
vault secrets enable -path=root-ca pki

vault secrets tune -max-lease-ttl=87600h root-ca

vault write -field=certificate root-ca/root/generate/internal \
  common_name="Acme Root CA" ttl=87600h > /vault/certs/root-ca.pem

vault write root-ca/config/urls \
  issuing_certificates="$VAULT_ADDR/v1/root-ca/ca" \
  crl_distribution_points="$VAULT_ADDR/v1/root-ca/crl"

vault secrets enable -path=int-ca pki

vault secrets tune -max-lease-ttl=43800h int-ca

vault write -field=csr int-ca/intermediate/generate/internal \
  common_name="Acme Intermediate CA" ttl=43800h > /vault/certs/int-ca.csr

vault write -field=certificate root-ca/root/sign-intermediate \
  csr=@/vault/certs/int-ca.csr format=pem_bundle ttl=43800h > /vault/certs/int-ca.pem

vault write int-ca/intermediate/set-signed \
  certificate=@/vault/certs/int-ca.pem

vault write int-ca/config/urls \
  issuing_certificates="$VAULT_ADDR/v1/int-ca/ca" \
  crl_distribution_points="$VAULT_ADDR/v1/int-ca/crl"

keytool -importcert -alias root-ca \
  -file /vault/certs/root-ca.pem \
  -keystore /vault/certs/truststore.jks \
  -storepass changeit \
  -trustcacerts -noprompt \
  -storetype JKS

keytool -importcert -alias int-ca \
  -file /vault/certs/int-ca.pem \
  -keystore /vault/certs/truststore.jks \
  -storepass changeit \
  -trustcacerts -noprompt \
  -storetype JKS

cp /vault/certs/truststore.jks /vault/secrets/

vault write int-ca/roles/zookeeper \
  allowed_domains="localhost,zookeeper-1,zookeeper-2,zookeeper-3" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=true client_flag=false \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth"

vault write -format=json int-ca/issue/zookeeper \
  common_name="zookeeper-1" \
  alt_names="localhost" \
  ip_sans="127.0.0.1" \
  > /vault/certs/zookeeper-1.json

jq -r ".data.private_key"  /vault/certs/zookeeper-1.json > /vault/certs/zookeeper-1.key
jq -r ".data.certificate"  /vault/certs/zookeeper-1.json > /vault/certs/zookeeper-1.crt
chmod 600 /vault/certs/zookeeper-1.key
chmod 600 /vault/certs/zookeeper-1.crt

openssl pkcs12 -export \
  -inkey    /vault/certs/zookeeper-1.key \
  -in       /vault/certs/zookeeper-1.crt \
  -certfile /vault/certs/int-ca.pem \
  -name zookeeper-1 \
  -out /vault/certs/zookeeper-1.p12 \
  -passout pass:changeit
chmod 644 /vault/certs/zookeeper-1.p12

vault write -format=json int-ca/issue/zookeeper \
  common_name="zookeeper-2" \
  alt_names="localhost" \
  ip_sans="127.0.0.1" \
  > /vault/certs/zookeeper-2.json

jq -r ".data.private_key"  /vault/certs/zookeeper-2.json > /vault/certs/zookeeper-2.key
jq -r ".data.certificate"  /vault/certs/zookeeper-2.json > /vault/certs/zookeeper-2.crt
chmod 600 /vault/certs/zookeeper-2.key
chmod 600 /vault/certs/zookeeper-2.crt

openssl pkcs12 -export \
  -inkey    /vault/certs/zookeeper-2.key \
  -in       /vault/certs/zookeeper-2.crt \
  -certfile /vault/certs/int-ca.pem \
  -name zookeeper-2 \
  -out /vault/certs/zookeeper-2.p12 \
  -passout pass:changeit
chmod 644 /vault/certs/zookeeper-2.p12

vault write -format=json int-ca/issue/zookeeper \
  common_name="zookeeper-3" \
  alt_names="localhost" \
  ip_sans="127.0.0.1" \
  > /vault/certs/zookeeper-3.json

jq -r ".data.private_key"  /vault/certs/zookeeper-3.json > /vault/certs/zookeeper-3.key
jq -r ".data.certificate"  /vault/certs/zookeeper-3.json > /vault/certs/zookeeper-3.crt
chmod 600 /vault/certs/zookeeper-3.key
chmod 600 /vault/certs/zookeeper-3.crt

openssl pkcs12 -export \
  -inkey    /vault/certs/zookeeper-3.key \
  -in       /vault/certs/zookeeper-3.crt \
  -certfile /vault/certs/int-ca.pem \
  -name zookeeper-3 \
  -out /vault/certs/zookeeper-3.p12 \
  -passout pass:changeit
chmod 644 /vault/certs/zookeeper-3.p12

vault write int-ca/roles/client \
  allowed_domains="localhost,client,ui,zoonavigator,kafka_connect,kafka-connect" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=false client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ClientAuth"

vault write -format=json int-ca/issue/client \
  common_name="client" \
  alt_names="localhost,client,ui,zoonavigator,kafka_connect,kafka-connect" \
  ip_sans="127.0.0.1" \
  > /vault/certs/client.json

jq -r ".data.private_key"   /vault/certs/client.json > /vault/certs/client.key
jq -r ".data.certificate"   /vault/certs/client.json > /vault/certs/client.crt
chmod 600 /vault/certs/client.key
chmod 600 /vault/certs/client.crt

openssl pkcs12 -export \
  -inkey /vault/certs/client.key \
  -in /vault/certs/client.crt \
  -certfile /vault/certs/int-ca.pem \
  -name client \
  -passout pass:changeit \
  -out /vault/certs/client.p12
chmod 644 /vault/certs/client.p12
cp /vault/certs/client.p12 /vault/secrets

vault write int-ca/roles/zoonavigator \
  allowed_domains="localhost,zoonavigator" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=false client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth"

vault write -format=json int-ca/issue/zoonavigator \
  common_name="zoonavigator" \
  alt_names="localhost" \
  ip_sans="127.0.0.1" \
  > /vault/certs/zoonavigator.json

jq -r ".data.private_key"   /vault/certs/zoonavigator.json > /vault/certs/zoonavigator.key
jq -r ".data.certificate"   /vault/certs/zoonavigator.json > /vault/certs/zoonavigator.crt
chmod 600 /vault/certs/zoonavigator.key
chmod 600 /vault/certs/zoonavigator.crt

openssl pkcs12 -export \
  -inkey /vault/certs/zoonavigator.key \
  -in /vault/certs/zoonavigator.crt \
  -certfile /vault/certs/int-ca.pem \
  -name zoonavigator \
  -passout pass:changeit \
  -out /vault/certs/zoonavigator.p12
chmod 644 /vault/certs/zoonavigator.p12

vault write int-ca/roles/kafka-broker \
  allowed_domains="localhost,kafka-1,kafka-2,kafka-3,kafka-replica-1,kafka-replica-2,kafka-replica-3" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=true client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth,ClientAuth"

vault write -format=json int-ca/issue/kafka-broker \
  common_name="kafka-1" \
  alt_names="localhost,kafka-1" \
  ip_sans="127.0.0.1" \
  > /vault/certs/kafka-1.json

jq -r ".data.private_key"  /vault/certs/kafka-1.json > /vault/certs/kafka-1.key
jq -r ".data.certificate"  /vault/certs/kafka-1.json > /vault/certs/kafka-1.crt
chmod 600 /vault/certs/kafka-1.crt
chmod 600 /vault/certs/kafka-1.key

openssl pkcs12 -export \
  -inkey    /vault/certs/kafka-1.key \
  -in       /vault/certs/kafka-1.crt \
  -certfile /vault/certs/int-ca.pem \
  -name kafka-1 \
  -passout pass:changeit \
  -out /vault/secrets/kafka-1.p12
chmod 644 /vault/secrets/kafka-1.p12

vault write -format=json int-ca/issue/kafka-broker \
  common_name="kafka-replica-1" \
  alt_names="localhost,kafka-replica-1" \
  ip_sans="127.0.0.1" \
  > /vault/certs/kafka-replica-1.json

jq -r ".data.private_key"  /vault/certs/kafka-replica-1.json > /vault/certs/kafka-replica-1.key
jq -r ".data.certificate"  /vault/certs/kafka-replica-1.json > /vault/certs/kafka-replica-1.crt
chmod 600 /vault/certs/kafka-replica-1.crt
chmod 600 /vault/certs/kafka-replica-1.key

openssl pkcs12 -export \
  -inkey    /vault/certs/kafka-replica-1.key \
  -in       /vault/certs/kafka-replica-1.crt \
  -certfile /vault/certs/int-ca.pem \
  -name kafka-replica-1 \
  -passout pass:changeit \
  -out /vault/secrets/kafka-replica-1.p12
chmod 644 /vault/secrets/kafka-replica-1.p12

vault write -format=json int-ca/issue/kafka-broker \
  common_name="kafka-2" \
  alt_names="localhost,kafka-2" \
  ip_sans="127.0.0.1" \
  > /vault/certs/kafka-2.json

jq -r ".data.private_key"  /vault/certs/kafka-2.json > /vault/certs/kafka-2.key
jq -r ".data.certificate"  /vault/certs/kafka-2.json > /vault/certs/kafka-2.crt
chmod 600 /vault/certs/kafka-2.crt
chmod 600 /vault/certs/kafka-2.key

openssl pkcs12 -export \
  -inkey    /vault/certs/kafka-2.key \
  -in       /vault/certs/kafka-2.crt \
  -certfile /vault/certs/int-ca.pem \
  -name kafka-2 \
  -passout pass:changeit \
  -out /vault/secrets/kafka-2.p12
chmod 644 /vault/secrets/kafka-2.p12

vault write -format=json int-ca/issue/kafka-broker \
  common_name="kafka-replica-2" \
  alt_names="localhost,kafka-replica-2" \
  ip_sans="127.0.0.1" \
  > /vault/certs/kafka-replica-2.json

jq -r ".data.private_key"  /vault/certs/kafka-replica-2.json > /vault/certs/kafka-replica-2.key
jq -r ".data.certificate"  /vault/certs/kafka-replica-2.json > /vault/certs/kafka-replica-2.crt
chmod 600 /vault/certs/kafka-replica-2.crt
chmod 600 /vault/certs/kafka-replica-2.key

openssl pkcs12 -export \
  -inkey    /vault/certs/kafka-replica-2.key \
  -in       /vault/certs/kafka-replica-2.crt \
  -certfile /vault/certs/int-ca.pem \
  -name kafka-replica-2 \
  -passout pass:changeit \
  -out /vault/secrets/kafka-replica-2.p12
chmod 644 /vault/secrets/kafka-replica-2.p12

vault write -format=json int-ca/issue/kafka-broker \
  common_name="kafka-3" \
  alt_names="localhost,kafka-3" \
  ip_sans="127.0.0.1" \
  > /vault/certs/kafka-3.json

jq -r ".data.private_key"  /vault/certs/kafka-3.json > /vault/certs/kafka-3.key
jq -r ".data.certificate"  /vault/certs/kafka-3.json > /vault/certs/kafka-3.crt
chmod 600 /vault/certs/kafka-3.crt
chmod 600 /vault/certs/kafka-3.key

openssl pkcs12 -export \
  -inkey    /vault/certs/kafka-3.key \
  -in       /vault/certs/kafka-3.crt \
  -certfile /vault/certs/int-ca.pem \
  -name kafka-3 \
  -passout pass:changeit \
  -out /vault/secrets/kafka-3.p12
chmod 644 /vault/secrets/kafka-3.p12

vault write -format=json int-ca/issue/kafka-broker \
  common_name="kafka-replica-3" \
  alt_names="localhost,kafka-replica-3" \
  ip_sans="127.0.0.1" \
  > /vault/certs/kafka-replica-3.json

jq -r ".data.private_key"  /vault/certs/kafka-replica-3.json > /vault/certs/kafka-replica-3.key
jq -r ".data.certificate"  /vault/certs/kafka-replica-3.json > /vault/certs/kafka-replica-3.crt
chmod 600 /vault/certs/kafka-replica-3.crt
chmod 600 /vault/certs/kafka-replica-3.key

openssl pkcs12 -export \
  -inkey    /vault/certs/kafka-replica-3.key \
  -in       /vault/certs/kafka-replica-3.crt \
  -certfile /vault/certs/int-ca.pem \
  -name kafka-replica-3 \
  -passout pass:changeit \
  -out /vault/secrets/kafka-replica-3.p12
chmod 644 /vault/secrets/kafka-replica-3.p12

vault write int-ca/roles/nifi \
  allowed_domains="localhost,nifi-1,nifi-2,nifi-3" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=true client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth,ClientAuth"

vault write -format=json int-ca/issue/nifi \
  common_name="nifi-1" \
  alt_names="localhost,nifi-1" \
  ip_sans="127.0.0.1" \
  > /vault/certs/nifi-1.json

jq -r ".data.private_key"  /vault/certs/nifi-1.json > /vault/certs/nifi-1.key
jq -r ".data.certificate"  /vault/certs/nifi-1.json > /vault/certs/nifi-1.crt
chmod 600 /vault/certs/nifi-1.crt
chmod 600 /vault/certs/nifi-1.key

openssl pkcs12 -export \
  -inkey    /vault/certs/nifi-1.key \
  -in       /vault/certs/nifi-1.crt \
  -certfile /vault/certs/int-ca.pem \
  -name nifi-1 \
  -passout pass:changeit \
  -out /vault/certs/nifi-1.p12
chmod 644 /vault/certs/nifi-1.p12

vault write -format=json int-ca/issue/nifi \
  common_name="nifi-2" \
  alt_names="localhost,nifi-2" \
  ip_sans="127.0.0.1" \
  > /vault/certs/nifi-2.json

jq -r ".data.private_key"  /vault/certs/nifi-2.json > /vault/certs/nifi-2.key
jq -r ".data.certificate"  /vault/certs/nifi-2.json > /vault/certs/nifi-2.crt
chmod 600 /vault/certs/nifi-2.crt
chmod 600 /vault/certs/nifi-2.key

openssl pkcs12 -export \
  -inkey    /vault/certs/nifi-2.key \
  -in       /vault/certs/nifi-2.crt \
  -certfile /vault/certs/int-ca.pem \
  -name nifi-2 \
  -passout pass:changeit \
  -out /vault/certs/nifi-2.p12
chmod 644 /vault/certs/nifi-2.p12

vault write -format=json int-ca/issue/nifi \
  common_name="nifi-3" \
  alt_names="localhost,nifi-3" \
  ip_sans="127.0.0.1" \
  > /vault/certs/nifi-3.json

jq -r ".data.private_key"  /vault/certs/nifi-3.json > /vault/certs/nifi-3.key
jq -r ".data.certificate"  /vault/certs/nifi-3.json > /vault/certs/nifi-3.crt
chmod 600 /vault/certs/nifi-3.crt
chmod 600 /vault/certs/nifi-3.key

openssl pkcs12 -export \
  -inkey    /vault/certs/nifi-3.key \
  -in       /vault/certs/nifi-3.crt \
  -certfile /vault/certs/int-ca.pem \
  -name nifi-3 \
  -passout pass:changeit \
  -out /vault/certs/nifi-3.p12
chmod 644 /vault/certs/nifi-3.p12

vault write int-ca/roles/schema-registry \
  allowed_domains="localhost,schema-registry" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=true client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth,ClientAuth"

vault write -format=json int-ca/issue/schema-registry \
  common_name="schema-registry" \
  alt_names="localhost,schema-registry" \
  ip_sans="127.0.0.1" \
  > /vault/certs/schema-registry.json

jq -r ".data.private_key"  /vault/certs/schema-registry.json > /vault/certs/schema-registry.key
jq -r ".data.certificate"  /vault/certs/schema-registry.json > /vault/certs/schema-registry.crt
chmod 600 /vault/certs/schema-registry.crt
chmod 600 /vault/certs/schema-registry.key

openssl pkcs12 -export \
  -inkey    /vault/certs/schema-registry.key \
  -in       /vault/certs/schema-registry.crt \
  -certfile /vault/certs/int-ca.pem \
  -name schema-registry \
  -passout pass:changeit \
  -out /vault/certs/schema-registry.p12
chmod 644 /vault/certs/schema-registry.p12
```

4. Скачать коннекторы для Kafka Connect:
```bash
mkdir confluent-hub-components
curl -O https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/3.2.0.Final/debezium-connector-postgres-3.2.0.Final-plugin.tar.gz
tar -xvf debezium-connector-postgres-3.2.0.Final-plugin.tar.gz
mv debezium-connector-postgres confluent-hub-components
curl -O https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.15.0/jmx_prometheus_javaagent-0.15.0.jar
mv jmx_prometheus_javaagent-0.15.0.jar kafka-connect

cp -r ../confluentinc-kafka-connect-hdfs3-2.0.3/ confluent-hub-components/

rm -rf debezium-connector-postgres-3.2.0.Final-plugin.tar.gz
```

5. Запустить сервисы Zookeeper, Kafka, Zoonavigator, Kafka UI:
```bash
sudo docker compose up zookeeper-1 zookeeper-2 zookeeper-3 zoonavigator kafka-1 kafka-2 kafka-3 kafka-replica-1 kafka-replica-2 kafka-replica-3 ui -d

# Zoonavigator будет доступен по адресу https://<your_host_ip>:9443. Мой адрес https://192.168.1.128:9443
# Connection string 'zookeeper-1:2281,zookeeper-2:2281,zookeeper-3:2281/kafka'
# Юзер и пароль для входа -  navigator:navigator_pass
```

6. Создать топики и раздать права в Kafka.
```bash
sudo docker compose exec -e KAFKA_OPTS="" -e KAFKA_JMX_OPTS="" kafka-1 bash -lc "
# UI
kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:ui \
  --operation Describe --operation DescribeConfigs \
  --cluster \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:ui \
  --operation Describe --operation DescribeConfigs \
  --cluster \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:ui \
  --operation Read --topic '*' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:ui \
  --operation Read --topic '*' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

# Schema
kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:schema \
  --operation Describe --operation Read --group 'schema-registry' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:schema \
  --operation Describe --operation Read --group 'schema-registry' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:schema \
  --operation All \
  --topic '_schemas' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:schema \
  --operation All \
  --topic '_schemas' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

# Connect
kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:connect \
  --operation Describe --operation Read --group 'kafka_connect' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:connect \
  --operation Describe --operation Read --group 'kafka_connect' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:connect \
  --operation Read --operation Write --operation Describe --operation Create \
  --topic 'connect-offset-storage' \
  --topic 'connect-status-storage' --topic 'connect-config-storage' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:connect \
  --operation Read --operation Write --operation Describe --operation Create \
  --topic 'connect-offset-storage' \
  --topic 'connect-status-storage' --topic 'connect-config-storage' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

# Mirror

kafka-topics --bootstrap-server kafka-1:9093 \
  --create --topic mirroring --partitions 3 \
  --replication-factor 3 \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:mirror \
  --operation Describe --operation Read --group 'mirroring' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:mirror \
  --operation Read \
  --topic 'mirroring' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:mirror \
  --operation Read --operation Write --operation Describe --operation Create \
  --topic 'source.mirroring' --topic 'mm2-offset-syncs.source.internal' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

# HDFS connector

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --add --allow-principal User:hdfs \
  --operation CREATE --operation DESCRIBE --cluster \
  --command-config adminclient-configs.conf

kafka-acls --bootstrap-server kafka-replica-1:9093 \
  --operation DESCRIBE --operation READ --operation WRITE --topic _confluent-command
  --add --allow-principal User:hdfs \
  --command-config adminclient-configs.conf

kafka-acls --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:hdfs \
  --operation Read \
  --topic 'source.mirroring' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf
"
```

7. Запустить остальные сервисы:
```bash
sudo docker compose up -d
```

8. Создать коннектор, проверить статус.
```bash
sudo docker compose exec -it kafka-connect bash -lc "
curl -X POST -H 'Content-Type: application/json' --data @/etc/kafka/connect.json http://localhost:8083/connectors
"
sudo docker compose exec -it kafka-connect bash -lc "
curl -X POST -H 'Content-Type: application/json' --data @/etc/kafka/hdfs-sync.json http://localhost:8083/connectors
"
sudo docker compose exec kafka-connect curl -s http://localhost:8083/connectors/mirror_connector/status | jq
sudo docker compose exec -e KAFKA_OPTS="" -e KAFKA_JMX_OPTS="" -it kafka-1 bash -lc "
kafka-console-producer \
  --bootstrap-server kafka-1:9093 \
  --producer.config /etc/kafka/secrets/adminclient-configs.conf \
  --topic mirroring 
"
sudo docker compose exec kafka-connect curl -s -X DELETE http://localhost:8083/connectors/mirror_connector
sudo docker compose exec kafka-connect curl -s -X DELETE http://localhost:8083/connectors/hdfs3-sync
```



