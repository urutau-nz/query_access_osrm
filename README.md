# Querying OSRM to determine proximity

## Check our [blog post at Urutau.](https://urutau.co.nz/how-to/osrm/)

This code can be used to calculate the open street map (OSM) network distance between a set of origins and a set of destinations.

The steps are
1. Set up an OSRM docker
1. (optional) Create a SQL database for where your results will be stored (instructions below)
1. (optional) Download the origin and destination cogit stordinates. These need to be added to the SQL
1. Create a config.yaml file
1. Run `main.py`


### Docker
The simplest way to locally host the server is through Docker. First install Docker on your computer. Then pull the image: `docker pull osrm/osrm-backend`. Further details [here](https://hub.docker.com/r/osrm/osrm-backend/).

### SQL Database (you can skip this step if you just want a OSRM server running)
Again, this will pull a docker from dockerhub. In the code below I'm pulling [a PostGreSQL PostGIS docker image](https://hub.docker.com/r/postgis/postgis). However there may be a preferable alternative when you read this - just search the docker.hub.com.

Firstly, create a docker container. If you're hosting this locally, just provide the port number, otherwise include the host:port:
```
docker run --name $db_name -p localport:5432 -v data:/var/lib/postgresql -e POSTGRES_PASSWORD='$yourpassword' -d postgis/postgis
```
Then you need to initiate PostGIS
```docker run -it --link $db_name:postgres --rm postgres sh -c 'exec psql -h "$POSTGRES_PORT_5432_TCP_ADDR" -p "$POSTGRES_PORT_5432_TCP_PORT" -U postgres'
CREATE DATABASE $db_name;
\c $db_name;
CREATE EXTENSION postgis;
\q
```

### Provide the origin and destination data (you can skip this step if you just want a OSRM server running)
As an example, you can push a shapefile to PostGreSQL DB using this command
`shp2pgsql -I -s $the_WKID $shapefilename.shp $db_table_name | psql -U postgres -d $db_name -h $host -p $port
`

### Our code
The code we provide automatically downloads the OpenStreetMap (OSM) data and intiates the OSRM server based on that network.
If you wish, you can then use the code to query a large number of origin-destination pairs.

You will need to update the config.yaml file to tell the code what region you want to download. Check the [geofabrik site](http://download.geofabrik.de/) for the right name formatting.

### Test
If you have a OSRM server running, you can test it through a URL request (either in the browser or command line).
It should be of this form `http://localhost:5000/route/v1/walking/-75.556521,39.746364;-75.545551,39.747228?overview=false
`.
Note, this is orig_lon, orig_lat; dest_lon, dest_lat (origin then destination).
