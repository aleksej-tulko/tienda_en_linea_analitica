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

# Серт зукипера

vault write kafka-int-ca/roles/zookeeper \
  allowed_domains="localhost,zookeeper" \
  allow_subdomains=true allow_bare_domains=true \
  allow_ip_sans=true allow_localhost=true \
  enforce_hostnames=false \
  server_flag=true client_flag=false \
  key_type="rsa" key_bits=2048 ttl="720h" max_ttl="720h" \
  key_usage="DigitalSignature,KeyEncipherment" \
  ext_key_usage="ServerAuth"


vault write -format=json kafka-int-ca/issue/zookeeper \
  common_name="zookeeper" \
  alt_names="zookeeper,localhost" \
  ip_sans="127.0.0.1" \
  > /vault/certs/zookeeper.json

jq -r ".data.private_key"  /vault/certs/zookeeper.json > /vault/certs/zookeeper.key
jq -r ".data.certificate"  /vault/certs/zookeeper.json > /vault/certs/zookeeper.crt
chmod 600 /vault/certs/zookeeper.key

openssl pkcs12 -export \
  -inkey    /vault/certs/zookeeper.key \
  -in       /vault/certs/zookeeper.crt \
  -certfile /vault/certs/kafka-int-ca.pem \
  -name zookeeper \
  -out /vault/certs/zookeeper.p12 \
  -passout pass:changeit


# Кейстор и трастстор

keytool -import -alias root-ca -trustcacerts -file /vault/certs/root-ca.pem -keystore kafka-truststore.jks -storepass changeit -noprompt


keytool -import -alias kafka-int-ca -trustcacerts -file /vault/certs/kafka-int-ca.pem -keystore kafka-truststore.jks -storepass changeit -noprompt