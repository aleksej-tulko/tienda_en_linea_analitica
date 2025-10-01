# tienda_en_linea_analitica


vault secrets enable -path=root-ca pki

vault secrets tune -max-lease-ttl=87600h root-ca

vault write -field=certificate root-ca/root/generate/internal \
  common_name="Acme Root CA" ttl=87600h > /vault/certs/root-ca.pem

vault write root-ca/config/urls \
  issuing_certificates="$VAULT_ADDR/v1/root-ca/ca" \
  crl_distribution_points="$VAULT_ADDR/v1/root-ca/crl"


# Корневой и промежеточкный серт

vault secrets enable -path=kafka-int-ca pki
vault secrets tune -max-lease-ttl=43800h kafka-int-ca

vault write -field=csr kafka-int-ca/intermediate/generate/internal \
  common_name="Acme Kafka Intermediate CA" ttl=43800h > /vault/certs/kafka-int-ca.csr

vault write -field=certificate root-ca/root/sign-intermediate \
  csr=@/vault/certs/kafka-int-ca.csr format=pem_bundle ttl=43800h > /vault/certs/kafka-int-ca.pem

vault write kafka-int-ca/intermediate/set-signed \
  certificate=@/vault/certs/kafka-int-ca.pem

vault write kafka-int-ca/config/urls \
  issuing_certificates="$VAULT_ADDR/v1/kafka-int-ca/ca" \
  crl_distribution_points="$VAULT_ADDR/v1/kafka-int-ca/crl"

# Роль зукипера

vault write kafka-int-ca/roles/zookeeper \
  allowed_domains="localhost,zookeeper-1,zookeeper-2,zookeeper-3" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=true client_flag=false \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth"


vault write -format=json kafka-int-ca/issue/zookeeper \
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
  -certfile /vault/certs/kafka-int-ca.pem \
  -name zookeeper-1 \
  -out /vault/certs/zookeeper-1.p12 \
  -passout pass:changeit
chmod 644 /vault/certs/zookeeper-1.p12

vault write -format=json kafka-int-ca/issue/zookeeper \
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
  -certfile /vault/certs/kafka-int-ca.pem \
  -name zookeeper-2 \
  -out /vault/certs/zookeeper-2.p12 \
  -passout pass:changeit
chmod 644 /vault/certs/zookeeper-2.p12

vault write -format=json kafka-int-ca/issue/zookeeper \
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
  -certfile /vault/certs/kafka-int-ca.pem \
  -name zookeeper-3 \
  -out /vault/certs/zookeeper-3.p12 \
  -passout pass:changeit
chmod 644 /vault/certs/zookeeper-3.p12


# Роль клиента

vault write kafka-int-ca/roles/client \
  allowed_domains="localhost,client,zoonavigator" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=false client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ClientAuth"


vault write -format=json kafka-int-ca/issue/client \
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
  -certfile /vault/certs/kafka-int-ca.pem \
  -name client \
  -passout pass:changeit \
  -out /vault/certs/client.p12
chmod 644 /vault/certs/client.p12


# Роль Zoonavigator

vault write kafka-int-ca/roles/zoonavigator \
  allowed_domains="localhost,zoonavigator" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=false client_flag=true \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth"

vault write -format=json kafka-int-ca/issue/zoonavigator \
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
  -certfile /vault/certs/kafka-int-ca.pem \
  -name zoonavigator \
  -passout pass:changeit \
  -out /vault/certs/zoonavigator.p12
chmod 644 /vault/certs/zoonavigator.p12


# Кейстор и трастстор

keytool -importcert -alias root-ca \
  -file /vault/certs/root-ca.pem \
  -keystore /vault/certs/kafka-truststore.jks \
  -storepass changeit \
  -trustcacerts -noprompt \
  -storetype JKS

keytool -importcert -alias kafka-int-ca \
  -file /vault/certs/kafka-int-ca.pem \
  -keystore /vault/certs/kafka-truststore.jks \
  -storepass changeit \
  -trustcacerts -noprompt \
  -storetype JKS