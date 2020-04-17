state = input('State: ')

import subprocess
from config import *
db, context = cfg_init(state)

state_name = context['state']
port = context['port']
transport_mode = 'car'
directory = '/homedirs/man112/osm_data'

subprocess.Popen(['/bin/bash','init_osrm.sh', state_name, port, transport_mode, directory, state])
