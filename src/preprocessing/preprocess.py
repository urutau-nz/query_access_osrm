# the query looks like this: '{}/route/v1/driving/{},{};{},{}?overview=false'.format(osrm_url, lon_o, lat_o, lon_d, lat_d)
# http://localhost:6014/route/v1/driving/{},{};{},{}


#Loc X: -90.071392618565, Loc Y: 30.01270094914956, dest X: -90.385078, dest Y29.901669
import requests

response = requests.get("http://localhost:6014/route/v1/driving/{},{};{},{}&annotations=true&steps=true".format(-90.071392618565, 30.01270094914956, -90.385078, 29.901669))

#http://project-osrm.org/docs/v5.15.2/api/?language=Python#waypoint-object

print(response.json())

'''
{
   "code":"Ok",
   "routes":[
      {
         "geometry":"ezdvD~cwdPfk@gHhTzT~jBeGhmB__A`\\u@rF}IlRnPfKiEng@jFySqp@pYcRvyC}GrvAxpCnj@hfDeNf@xH`[lCrjA{i@|uByN~RchAf^ob@dgB^vuApi@dRdTO`HllBeKfZfB`\\}E`i@oVxd@cj@hb@gfCd|@yRbOgm@~gAuKjz@pKd_Bt]`zApe@~z@f_C`kCvJhw@oA|vBaVzjB~iEhuCzHcDyGcO",
         "legs":[
            {
               "steps":[],
               "distance":54765.5,
               "duration":39434.4,
               "summary":"",
               "weight":39434.4
            }
         ],
         "distance":54765.5,
         "duration":39434.4,
         "weight_name":"duration",
         "weight":39434.4
      }
   ],
   "waypoints":[
      {
         "hint":"SvoHgJX6B4CLAgAAlAIAAAAAAAAAAAAA_km0QqODtkIAAAAAAAAAAIsCAACUAgAAAAAAAAAAAAABAAAA5Zyh-gH1yQGfnqH6HfXJAQAA_wrbHa5x",
         "distance":42.749924,
         "name":"Charlotte Drive",
         "location":[
            -90.071835,
            30.012673
         ]
      },
      {
         "hint":"O1cKgD5XCoC5AAAAEAEAAAAAAAAAAAAAyTHNQTxlFkIAAAAAAAAAALkAAAAQAQAAAAAAAAAAAAABAAAAStWc-mVDyAFK1Zz6ZUPIAQAAnwHbHa5x",
         "distance":0,
         "name":"Magnolia Avenue",
         "location":[
            -90.385078,
            29.901669
         ]
      }
   ]
}
'''
