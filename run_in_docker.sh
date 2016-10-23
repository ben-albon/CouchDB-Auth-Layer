#!/bin/bash

# You can use this script to run your own locally built docker container

# If you are running couchdb-auth-layer inside a container, that container will need to be able to connect to a session database, and (of course) a couchdb instance
COUCHDB='mycouchdb-container'
SESSIONDB='mysessiondb-container'
LINKS="--link my-session-db-container:db.example.com"
PORT_MAPPINGS="-p 5984:5984"
docker run -it -ephemeral --rm --link ${COUCHDB} --link ${SESSIONDB} --name mycouchdbauthlayer-container couchdb-auth-layer
