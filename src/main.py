import init_osrm
import query
import yaml
import subprocess
# functions - logging
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

def single_region():
    # establish config filename
    config_filename = input('Insert Config Filename (filename.yaml): ')
    if ('yaml' in config_filename) == True:
        config_filename = config_filename[:-5]
    # run
    query_osrm(config_filename)


def multi_regions():
    # establish config filenames
    states = ['il','md','fl', 'co', 'mi', 'la', 'ga', 'or', 'wa', 'tx']
    for state in states:
        config_filename = state
        # run
        query_osrm(config_filename)


def query_osrm(config_filename):
    # import config file
    with open('./src/config/{}.yaml'.format(config_filename)) as file:
        config = yaml.load(file)

    # initialize the OSRM server
    logger.info('Initialize the OSRM server for {} to {} in {}'.format(config['transport_mode'], config['services'],config['location']['city']))
    init_osrm.main(config, logger)
    logger.info('OSRM server initialized')

    # query the OSRM server
    query.main(config)

    # shutdown the OSRM server
    if config['OSRM']['shutdown']:
        shell_commands = [
                            'docker stop osrm-{}'.format(config['location']['state']),
                            'docker rm osrm-{}'.format(config['location']['state']),
                            ]
        for com in shell_commands:
            com = com.split()
            subprocess.run(com)
    logger.info('OSRM server shutdown and removed')

if __name__ == '__main__':
    single_region()
