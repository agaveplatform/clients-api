#!/bin/bash

fig up -d
echo "Waiting for services to start..."
sleep 5
echo "Adding tenant1 ou and jdoe user..."
curl -X POST --data ou=tenant1 localhost:8000/ous
curl -X POST --data "username=jdoe&password=abcde&email=jdoe@test.com" localhost:8000/profiles/v2

echo ""
echo ""
echo "The following services are now running:"
echo "agave_id      -> 8000"
echo "agave_clients -> 8001"
echo "mysql         -> 3306"
echo "ldap          -> 10389"
echo "You can now try out the services."
echo "Examples:"
echo "curl localhost:8001/profiles/v2/"
echo ""
echo "Stop the services with fig stop."
