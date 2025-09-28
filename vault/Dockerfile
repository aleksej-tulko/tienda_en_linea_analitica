FROM hashicorp/vault

RUN apk add jq openssl openjdk17

RUN mkdir /vault/certs

RUN mkdir /vault/secrets

COPY ./configs/ /vault/config/

RUN chown 100:1000 /vault -R