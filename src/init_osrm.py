import subprocess
import os

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
    state = config['location']['state']

    # in shell, download the data and init the OSRM server
    shell_commands = [
                    # stop any existing dockers
                    'docker stop osrm-{}'.format(state),
                    'docker rm osrm-{}'.format(state),
                    # download the files
                    'rm -f {}/{}-latest*'.format(directory, state_name),
                    'wget -N https://download.geofabrik.de/{}/{}/{}-latest.osm.pbf -P {}'.format(continent, country, state_name, directory),
                    'echo "building files . . . "',
                    ]
    for com in shell_commands:
        com = com.split()
        subprocess.run(com)

    shell_commands = [
                    # init docker data
                    'docker run -t -v {}:/data osrm/osrm-backend osrm-extract -p /opt/{}.lua /data/{}-latest.osm.pbf'.format(directory, transport_mode, state_name),
                    'docker run -t -v {}:/data osrm/osrm-backend osrm-partition /data/{}-latest.osrm'.format(directory, state_name),
                    'docker run -t -v {}:/data osrm/osrm-backend osrm-customize /data/{}-latest.osrm'.format(directory, state_name),
                    'docker run -d --name osrm-{} -t -i -p {}:5000 -v {}:/data osrm/osrm-backend osrm-routed --algorithm mld --max-table-size 100000 /data/{}-latest.osrm'.format(state, port, directory, state_name),
                    ]
    for com in shell_commands:
        com = com.split()
        subprocess.run(com, stdout=open(os.devnull, 'wb'))

    shell_commands = [
                    # start docker
                    'docker run -d --name osrm-{} -t -i -p {}:5000 -v {}:/data osrm/osrm-backend osrm-routed --algorithm mld --max-table-size 100000 /data/{}-latest.osrm'.format(state, port, directory, state_name),
                    'echo ". . . docker initialized . . ."',
                    ]
    for com in shell_commands:
        com = com.split()
        subprocess.run(com)
