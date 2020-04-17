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
#plotting
from scipy.integrate import simps
import matplotlib.pyplot as plt
import random
import seaborn as sns
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
        context['city'] = 'Baltimore'
        context['state'] = 'maryland'
        # url to the osrm routing machine
        context['port'] = '6003'
        context['services'] = ['supermarket', 'school', 'hospital', 'library']
    elif state == 'wa':
        db['name'] = 'access_wa'
        context['city_code'] = 'sea'
        context['city'] = 'Seattle'
        context['state'] = 'washington'
        # url to the osrm routing machine
        context['port'] = '6004'
        context['services'] = ['supermarket', 'school', 'hospital', 'library']
    elif state == 'nc':
        db['name'] = 'access_nc'
        context['city_code'] = 'wil'
        context['city'] = 'wilmington'
        context['state'] = 'north-carolina'
        # url to the osrm routing machine
        context['port'] = '6002'
        context['services'] = ['super_market_operating', 'gas_station']
    elif state == 'il':
        db['name'] = 'access_il'
        context['city_code'] = 'chi'
        context['city'] = 'Chicago'
        context['state'] = 'illinois'
        context['port'] = '6005'
        context['services'] = ['supermarket']
    elif state == 'tx':
        db['name'] = 'access_tx'
        context['city_code'] = 'hou'
        context['city'] = 'Houston'
        context['state'] = 'texas'
        context['port'] = '6006'
        context['services'] = ['supermarket']
        context['services'] = ['supermarket']
    elif state == 'or':
        db['name'] = 'access_or'
        context['city_code'] = 'por'
        context['city'] = 'Portland'
        context['state'] = 'oregon'
        context['port'] = '6007'
        context['services'] = ['supermarket']
    elif state == 'ga':
        db['name'] = 'access_ga'
        context['city_code'] = 'atl'
        context['city'] = 'Atlanta'
        context['state'] = 'georgia'
        context['port'] = '6008'
        context['services'] = ['supermarket']
    elif state == 'la':
        db['name'] = 'access_la'
        context['city_code'] = 'new'
        context['city'] = 'New_Orleans'
        context['state'] = 'louisiana'
        context['port'] = '6009'
        context['services'] = ['supermarket']
    elif state == 'mi':
        db['name'] = 'access_mi'
        context['city_code'] = 'det'
        context['city'] = 'Detroit'
        context['state'] = 'michigan'
        context['port'] = '6010'
        context['services'] = ['supermarket']
    elif state == 'co':
        db['name'] = 'access_co'
        context['city_code'] = 'den'
        context['city'] = 'Denver'
        context['state'] = 'colorado'
        context['port'] = '6011'
        context['services'] = ['supermarket']
    elif state == 'fl':
        db['name'] = 'access_fl'
        context['city_code'] = 'mia'
        context['city'] = 'Miami'
        context['state'] = 'florida'
        context['port'] = '6012'
        context['services'] = ['supermarket']
    elif state == 'ca':
        db['name'] = 'access_ca'
        context['city_code'] = 'san'
        context['city'] = 'San_Francisco'
        context['state'] = 'california'
        context['port'] = '6013'
        context['services'] = ['supermarket','hospital']
    elif state == 'test':
        db['name'] = 'access_la'
        context['city_code'] = 'new'
        context['port'] = '6014'
        context['city'] = 'New_Orleans'
        context['state'] = 'louisiana'
        context['services'] = ['supermarket']

    context['osrm_url'] = 'http://localhost:' + context['port']
    # connect to database
    db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
    db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
    db['con'] = psycopg2.connect(db['address'])
    return(db, context)
