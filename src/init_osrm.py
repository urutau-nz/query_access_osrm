state = input('State: ')

import subprocess
from config import *
db, context = cfg_init(state)

state_name = context['state']
port = context['port']
transport_mode = 'car'
directory = '/homedirs/man112/osm_data'


import subprocess
print "start"
# subprocess.call("sleep.sh")
subprocess.check_call("./init_osrm.sh %s %s %s %s %s" % (state_name, port, transport_mode, directory, state))
print "end"
