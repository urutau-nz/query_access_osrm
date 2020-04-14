# the query looks like this: '{}/route/v1/driving/{},{};{},{}?overview=false'.format(osrm_url, lon_o, lat_o, lon_d, lat_d)
# http://localhost:6014/route/v1/driving/{},{};{},{}

import requests

response = requests.get("http://localhost:6014/route/v1/driving/{},{};{},{}".format())