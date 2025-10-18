#!/bin/bash
set -e


mkdir -p /usr/local/hadoop/hdfs/namenode
chmod -R 777 /usr/local/hadoop/hdfs/namenode

hdfs namenode -format
hdfs --daemon start namenode
hdfs --daemon start secondarynamenode
yarn --daemon start resourcemanager

exec "$@"