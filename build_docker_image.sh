#!/bin/bash
cd "$(dirname "$0")"
docker build -t python-couchdb-auth-layer .