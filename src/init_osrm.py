import subprocess



def main(config):
    ''' run the shell script that
    - removes the existing docker
    - downloads the osrm files
    - establishes the osrm routing docker
    '''
    # transport mode options
    mode_dict = {'driving':'car','walking':'foot','cycling':'bicycle'}

    # pull the variables from the config file
    state_name = config['OSM']['state']
    continent = config['OSM']['continent']
    country = config['OSM']['country']
    port = config['OSRM']['port']
    transport_mode = mode_dict[config['transport_mode']]
    directory = config['OSM']['data_directory']

    # in shell, download the data and init the OSRM server
    subprocess.call(['/bin/bash', '/homedirs/man112/access_query_osrm/src/init_osrm.sh', state_name, port, transport_mode, directory, state, continent, country])
