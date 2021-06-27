#!/bin/bash

if [ "$HOST" != "" ]
then
  echo "HOST variable is set to $HOST"
  cqlsh "$HOST" -f ./cassandra_db_create.cql
else
  echo "HOST variable is not set"
fi
