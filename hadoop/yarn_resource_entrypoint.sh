#!/bin/bash
set -e

yarn resourcemanager
exec "$@"