#!/bin/bash
set -e


mkdir -p /usr/local/hadoop/hdfs/datanode
chmod -R 777 /usr/local/hadoop/hdfs/datanode

hdfs --daemon start datanode
yarn --daemon start nodemanager

exec "$@"