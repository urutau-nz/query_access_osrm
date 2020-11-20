import subprocess
from config import *

mode_dict = {'driving':'car','walking':'foot','cycling':'bicycle'}

def main(state, context, mode):
    ''' run the shell script that
    - removes the existing docker
    - downloads the osrm files
    - establishes the osrm routing docker
    '''
    context = cfg_init(state)[1]

    state_name = context['state']
    continent = context['continent']
    port = context['osrm_url'][-4:]
    transport_mode = mode_dict[mode]
    directory = '/homedirs/man112/osm_data'

    subprocess.call(['/bin/bash', '/homedirs/man112/access_query_osrm/src/init_osrm.sh', state_name, port, transport_mode, directory, state, continent])



# if __name__ == "__main__":
#     state = input('State: ')
#     main(state)
