#!/bin/bash


echo "state code: $1"

docker stop osrm-$1
docker rm osrm-$1

echo "Docker Container Removed"
