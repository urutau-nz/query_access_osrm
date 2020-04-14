# the query looks like this: '{}/route/v1/driving/{},{};{},{}?overview=false'.format(osrm_url, lon_o, lat_o, lon_d, lat_d)
# http://localhost:6014/route/v1/driving/{},{};{},{}


#Loc X: -90.071392618565, Loc Y: 30.01270094914956, dest X: -90.116577, dest Y-90.116577
import requests

response = requests.get("http://localhost:6014/route/v1/driving/{},{};{},{}".format(-90.071392618565, 30.01270094914956, -90.116577, -90.116577))

print(response)