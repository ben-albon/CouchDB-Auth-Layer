#!/bin/bash
LINKS="--link my-session-db-container:db.example.com"
PORT_MAPPINGS="-p 5984:5984"
docker run -it --rm ${LINKS} ${PORT_MAPPINGS} --name db-auth-layer python-couchdb-auth-layer
