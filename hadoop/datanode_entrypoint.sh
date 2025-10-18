#!/bin/bash
set -e


mkdir -p /usr/local/hadoop/hdfs/datanode
chmod -R 777 /usr/local/hadoop/hdfs/datanode

mkdir -p /opt/hadoop/yarn/local /opt/hadoop/yarn/logs
chmod -R 777 /opt/hadoop/yarn

yarn --daemon start nodemanager

exec "$@"