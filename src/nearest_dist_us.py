'''
Populate the database for the nearest proximity throughout time
'''
import code
import pickle as pk
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy.engine import create_engine
from datetime import datetime, timedelta
import itertools
import time
import pandas as pd
import geopandas as gpd
from tqdm import tqdm

# SQL connection
passw = open('pass.txt', 'r').read().strip('\n')
host = '132.181.102.2'
port = '5001'

# city information
state = input('State: ')
if state == 'md':
    db_name = 'access_md'
    city = 'bal'
    # url to the osrm routing machine
    osrm_url = 'http://localhost:6003'
    services = ['supermarket', 'school', 'hospital', 'library']
elif state == 'wa':
    db_name = 'access_wa'
    city = 'sea'
    # url to the osrm routing machine
    osrm_url = 'http://localhost:6004'
    services = ['supermarket', 'school', 'hospital', 'library']
elif state == 'nc':
    db_name = 'access_nc'
    city = 'wil'
    # url to the osrm routing machine
    osrm_url = 'http://localhost:6002'
    services = ['super_market_operating', 'gas_station']
elif state == 'il':
    db_name = 'access_il'
    city = 'chi'
    city_full = 'Chicago'
    osrm_url = 'http://localhost:6005'
    services = ['supermarket']
elif state == 'tx':
    db_name = 'access_tx'
    city = 'hou'
    city_full = 'Houston'
    osrm_url = 'http://localhost:6006'
    services = ['supermarket']
    services = ['supermarket']
elif state == 'or':
    db_name = 'access_or'
    city = 'por'
    city_full = 'Portland'
    osrm_url = 'http://localhost:6007'
    services = ['supermarket']
elif state == 'ga':
    db_name = 'access_ga'
    city = 'atl'
    city_full = 'Atlanta'
    osrm_url = 'http://localhost:6008'
    services = ['supermarket']
elif state == 'la':
    db_name = 'access_la'
    city = 'new'
    city_full = 'New_Orleans'
    osrm_url = 'http://localhost:6009'
    services = ['supermarket']
elif state == 'mi':
    db_name = 'access_mi'
    city = 'det'
    city_full = 'Detroit'
    osrm_url = 'http://localhost:6010'
    services = ['supermarket']
elif state == 'co':
    db_name = 'access_co'
    city = 'den'
    city_full = 'Denver'
    osrm_url = 'http://localhost:6011'
    services = ['supermarket']
elif state == 'fl':
    db_name = 'access_fl'
    city = 'mia'
    city_full = 'Miami'
    osrm_url = 'http://localhost:6012'
    services = ['supermarket']


# connect to database
engine = create_engine('postgresql+psycopg2://postgres:' + passw + '@' + host + '/' + db_name + '?port=' + port)
connect_string = "host=" + host + " dbname=" + db_name + " user=postgres password='"+ passw + "' port=" + port

con = psycopg2.connect(connect_string)
cursor = con.cursor()

def populate_database():
    '''
    determine closest services for time = 0 (initial case), all ids are open
    '''
    #get destination ids
    outs = {}

    for service in services:
        # outs[service] = import_outages(service)
        sql = "SELECT id FROM destinations WHERE dest_type = %s;"
        dests = pd.read_sql(sql, con, params = (service,))
        dest_ids = dests.id.values
        outs[service] = {'0':dest_ids}

    # init the dataframe
    df = pd.DataFrame(columns = ['id_orig','distance','service', 'time_stamp', 'sim_num', 'metric'])
    # get the times
    times = sorted(outs[services[0]].keys()) #times is just ['0'] in this initial case
    time_stamp = times[0] #because this is the initial case where everything is open
    # get the distance matrix
    distances = pd.read_sql('SELECT * FROM distance', con)
    #making the id_dest column the index
    distances = distances.set_index('id_dest')
    #converts distance column from string to float
    distances.distance = pd.to_numeric(distances.distance)

    # block ids
    id_orig = np.unique(distances.id_orig)

    # loop services
    for i in tqdm(range(len(services))):
        service = services[i]
        ids_open = outs[service][time_stamp]
        # subset the distance matrix on dest_id
        dists_sub = distances.loc[ids_open]
        # get the minimum distance
        df_min = dists_sub.groupby('id_orig')['distance'].min()
        # prepare df to append: This makes distance the name of the column not the series
        df_min = df_min.to_frame('distance')
        df_min.reset_index(inplace=True)

        # prepare df to append. Adding these columns as they are needed in simulation.py
        df_min['service'] = service
        df_min['time_stamp'] = time_stamp
        df_min['sim_num'] = 0
        df_min['metric'] = 0
        # append
        df = df.append(df_min, ignore_index=True)
    #sorts by id_orig
    df.sort_values(by=['id_orig', 'service'], inplace=True)
    # add df to sql, if it exists it will be replaced
    df.to_sql('nearest_dist', con=engine, if_exists='replace', index=False)
    # add index
    cursor.execute('CREATE INDEX on nearest_dist (time_stamp);')
    # commit
    con.commit()

#I havn't used this function
def init_df(services, outs):
    '''
    initialize the dataframe for storing the temporal proximity data
    '''
    # get the times
    times = sorted(outs[services[0]].keys())
    # get the block ids
    sql = "SELECT block.geoid10 FROM block, city WHERE ST_Intersects(block.geom, ST_Transform(city.geom, 4269)) AND city.juris = 'WM'"
    cursor.execute(sql)
    orig_ids = cursor.fetchall()
    orig_ids = [x[0] for x in orig_ids]
    # init the df
    df = pd.DataFrame(list(itertools.product(orig_ids, times, services)), columns = ['id_orig','time_stamp','service'])
    # add additional columns
    df['distance'] = None
    df['id_dest'] = None
    return(df)

if __name__ == "__main__":
    populate_database()
