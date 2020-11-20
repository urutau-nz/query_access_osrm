#!/bin/bash

echo "state: $1"
echo "port: $2"
echo "transport mode: $3"
echo "directory: $4"
echo "state code: $5"
echo "continent: $6"

docker stop osrm-$5
docker rm osrm-$5

cd $4

echo $PWD
echo change directory to $PWD

echo "downloading files . . . "
rm -f $1-latest*
wget -N https://download.geofabrik.de/$6/$1-latest.osm.pbf

docker run -t -v $4:/data osrm/osrm-backend osrm-extract -p /opt/$3.lua /data/$1-latest.osm.pbf
docker run -t -v $4:/data osrm/osrm-backend osrm-partition /data/$1-latest.osrm
docker run -t -v $4:/data osrm/osrm-backend osrm-customize /data/$1-latest.osrm

docker run -d --name osrm-$5 -t -i -p $2:5000 -v $4:/data osrm/osrm-backend osrm-routed --algorithm mld --max-table-size 100000 /data/$1-latest.osrm
echo ". . . docker initialized . . ."
