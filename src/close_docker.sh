#!/bin/bash


echo "Removing Docker Container"

docker stop osrm-$1
docker rm osrm-$1

echo "Docker Container Removed"
