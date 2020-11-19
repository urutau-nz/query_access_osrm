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

    if sim == True:
        subprocess.call(['/bin/bash', '/homedirs/man112/monte_christchurch/src/init_osrm_sim.sh', state_name, port, transport_mode, directory, state, continent])

# if __name__ == "__main__":
#     state = input('State: ')
#     main(state)
