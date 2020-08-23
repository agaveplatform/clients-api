# Agave Clients #

## Overview ##

This project provides a web service for managing Agave OAuth2 clients and their subscriptions. It relies on an instance
of WSO2 API Manager and presumes the application data are stored in a MySQL database.

## Deploying with Docker Compose ##

You can start up the entire Agave Auth infrastructure (including the clients service) with the startup.sh script
provided in the deployment directory of this repository. The only dependencies are Docker and Docker Compose. Install each
and then execute:

```
#!bash

deployment/startup.sh
```

In addition to the clients service, the oauth infrastructure (apim and mysql) and the hosted identity infrastructure
(agave_id and ldap) will be started as well.

## Deploying with Docker ##
You can deploy an instance of the Agave Clients service on your local machine with a single command: the only dependency is docker. Simply execute:

```
#!bash

docker run -d -p 8000:80 agaveplatform/agave_clients:latest
```

This will start up an instance of the service in a container fronted by Apache web server listening on port 8000.
In fact, the image is hosted publicly on the docker hub so you don't even need to clone this repository to run the
command.