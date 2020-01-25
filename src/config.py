'''
Imports functions and variables that are common throughout the project
'''

# functions - data analysis
import numpy as np
import pandas as pd
import itertools
# functions - geospatial
import geopandas as gpd
# functions - data management
import pickle as pk
import psycopg2
from sqlalchemy.engine import create_engine
# functions - coding
import code
import os
from datetime import datetime, timedelta
import time
from tqdm import tqdm
# logging
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

def cfg_init(state):
    # SQL connection
    db = dict()
    db['passw'] = open('pass.txt', 'r').read().strip('\n')
    db['host'] = '132.181.102.2'
    db['port'] = '5001'
    # city information
    context = dict()
    if state == 'md':
        db['name'] = 'access_md'
        context['city_code'] = 'bal'
        context['city'] = 'baltimore'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6003'
        context['services'] = ['supermarket', 'school', 'hospital', 'library']
    elif state == 'wa':
        db['name'] = 'access_wa'
        context['city_code'] = 'sea'
        context['city'] = 'seattle'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6004'
        context['services'] = ['supermarket', 'school', 'hospital', 'library']
    elif state == 'nc':
        db['name'] = 'access_nc'
        context['city_code'] = 'wil'
        context['city'] = 'wilmington'
        # url to the osrm routing machine
        context['osrm_url'] = 'http://localhost:6002'
        context['services'] = ['super_market_operating', 'gas_station']
    elif state == 'il':
        db['name'] = 'access_il'
        context['city_code'] = 'chi'
        context['city'] = 'Chicago'
        context['osrm_url'] = 'http://localhost:6005'
        context['services'] = ['supermarket']
    # connect to database
    db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
    db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
    db['con'] = psycopg2.connect(db['address'])
    return(db, context)
