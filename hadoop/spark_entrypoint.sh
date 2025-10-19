#!/bin/bash
set -e


mkdir -p /opt/hadoop/conf
mkdir -p /opt/yarn/conf
chmod -R 777 /opt/hadoop/conf
chmod -R 777 /opt/yarn/conf

exec "$@"