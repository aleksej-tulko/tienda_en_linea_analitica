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

# ПУНКТЫ 3-12 ВЫПОЛНЯТЬ В ШЕЛЛЕ VAULT!!!!
```

3. Настроить Vault для создания корневого сертификата:

```bash
vault secrets enable -path=root-ca pki
vault secrets tune -max-lease-ttl=87600h root-ca
vault write -field=certificate root-ca/root/generate/internal \
  common_name="Acme Root CA" ttl=87600h > /vault/certs/root-ca.pem
vault write root-ca/config/urls \
  issuing_certificates="$VAULT_ADDR/v1/root-ca/ca" \
  crl_distribution_points="$VAULT_ADDR/v1/root-ca/crl"
```

4. Настроить Vault для создания промежуточного сертификата:

```bash
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
```

5. Создать роли для выпуска конечных сертификатов,сгенерировать сами сертификаты и собрать keystore для сервисов:

```bash
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
  allowed_domains="localhost,client,ui,zoonavigator" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=false client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ClientAuth"

vault write -format=json int-ca/issue/client \
  common_name="client" \
  alt_names="localhost" \
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
  allowed_domains="localhost,kafka-1,kafka-2,kafka-3" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=true client_flag=false \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth,ClientAuth"

vault write -format=json int-ca/issue/kafka-broker \
  common_name="kafka-1" \
  alt_names="localhost" \
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
  common_name="kafka-2" \
  alt_names="localhost" \
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
  common_name="kafka-3" \
  alt_names="localhost" \
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
```

6. Собрать truststore:
```bash
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

cp /vault/certs/truststore.jks /vault/secrets
```

7. Запустить сервисы Zookeeper, Kafka, Zoonavigator, Kafka UI
```bash
sudo docker compose up zookeeper-1 zookeeper-2 zookeeper-3 zoonavigator kafka-1 kafka-2 kafka-3 ui
```

8. Раздать права в Kafka
```bash
sudo docker compose exec -it kafka-1 kafka-acls \
  --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:ui \
  --operation Describe --operation DescribeConfigs \
  --cluster \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

sudo docker compose exec -it kafka-1 kafka-acls   --bootstrap-server kafka-1:9093   --add --allow-principal User:ui   --operation DescribeConfigs   --cluster   --command-config /etc/kafka/secrets/adminclient-configs.conf

sudo docker compose exec -it kafka-1 kafka-acls \
  --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:ui \
  --operation Read --topic '*' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf

sudo docker compose exec -it kafka-1 kafka-acls \
  --bootstrap-server kafka-1:9093 \
  --add --allow-principal User:ui \
  --operation Describe --group '*' \
  --command-config /etc/kafka/secrets/adminclient-configs.conf
```