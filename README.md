# An index for urban inequality:
## Case study on USA supermarket access


psql -h 132.181.102.2 -p 5001 -U postgres -W
#code.interact(local=locals())


`docker run --name osrm-fl -t -i -p 6012:5000 -v /homedirs/man112/osm_data:/data osrm/osrm-backend osrm-routed --algorithm mld --max-table-size 100000 /data/florida-latest.osrm`

init_osrm.main(state)
query.main(state)


```
import init_osrm
import query
from config import *

states = ['il','md','fl', 'co', 'mi', 'la', 'ga', 'or', 'wa', 'tx']

for state in states:
  init_osrm.main(state)
  query.main(state)



```
