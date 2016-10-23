#!/bin/bash

# You can use this script to build your own docker image from scratch

cd "$(dirname "$0")"
docker build -t couchdb-auth-layer .
