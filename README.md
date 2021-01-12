# Querying OSRM to determine proximity

## Check our [blog post at Urutau.](https://urutau.co.nz/how-to/osrm/)

This code can be used to calculate the open street map (OSM) network distance between a set of origins and a set of destinations.

The steps are
1. Ensure Docker is installed on your OS
1. Download the origin and destination shapefiles. Origins are usually polygons. Destinations are points.
1. Create a config.yaml file
1. Run `main.py`

This code then creates an OSRM docker for the network distance calculations. It creates a PostGreSQL database and uploads the origin and destination data in there. Then it runs the queries. 
Additional steps that are omitted include adding the demographic information to the origins and determining the nearest destination.


### Docker
The simplest way to locally host the server is through Docker. First install Docker on your computer. Then pull the image: `docker pull osrm/osrm-backend`. Further details [here](https://hub.docker.com/r/osrm/osrm-backend/).

### Our code
The code we provide automatically downloads the OpenStreetMap (OSM) data and intiates the OSRM server based on that network.
If you wish, you can then use the code to query a large number of origin-destination pairs.

You will need to update the config.yaml file to tell the code what region you want to download. Check the [geofabrik site](http://download.geofabrik.de/) for the right name formatting.

### Test
If you have a OSRM server running, you can test it through a URL request (either in the browser or command line).
It should be of this form `http://localhost:5000/route/v1/walking/-75.556521,39.746364;-75.545551,39.747228?overview=false
`.
Note, this is orig_lon, orig_lat; dest_lon, dest_lat (origin then destination).
