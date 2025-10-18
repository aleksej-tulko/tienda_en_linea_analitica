#!/bin/bash
set -e

yarn nodemanager
exec "$@"