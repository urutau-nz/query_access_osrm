'''
Init the database
Query origin-destination pairs using OSRM
'''
############## Imports ##############
# Packages
import math
import os.path
import io
import numpy as np
import pandas as pd
import itertools
from datetime import datetime
import subprocess
# functions - geospatial
import osgeo.ogr
import geopandas as gpd
import shapely
from geoalchemy2 import Geometry, WKTElement
# functions - data management
import psycopg2
from sqlalchemy.types import Float, Integer
from sqlalchemy.engine import create_engine
# functions - parallel
import multiprocessing as mp
from joblib import Parallel, delayed
from tqdm import tqdm
# functions - requests
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
# functions - logging
import logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

############## Main ##############
def main(config):
    '''
    gathers context and runs functions based on 'script_mode'
    '''
    # gather data and context
    db = init_db(config)

    # Place destinations in SQL
    if config['set_up']['destination_file_directory'] != False:
        # init the destination tables
        create_dest_table(db, config)
        logger.info('Successfully exported destination shapefile to SQL')
    # Place origin blocks in SQL
    if config['set_up']['origin_file_directory'] != False:
        #create_origin_table(db, config)
        export_origin = 'shp2pgsql -I -s {} {} block_test_one | psql -U postgres -d access_{} -h 132.181.102.2 -p 5001'.format(config['set_up']['projection'], config['set_up']['origin_file_directory'], config['location']['state'])
        print(export_origin)
        command = subprocess.Popen(export_origin.split(), stdout=open(os.devnull, 'wb'))
        command.communicate(input=open('pass.txt', 'r').read().strip('\n'))
        logger.info('Successfully exported origin block shapefile to SQL')


    # query the distances
    logger.info('Querying invoked for {} in {}'.format(config['transport_mode'], config['location']['state']))
    origxdest = query_points(db, config)
    # add df to sql
    write_to_postgres(origxdest, db)

    # close the connection
    db['con'].close()
    logger.info('Database connection closed')

def init_db(config):
    # SQL connection
    db = config['SQL'].copy()
    db['name'] = 'access_{}'.format(config['location']['state'])
    db['passw'] = open('pass.txt', 'r').read().strip('\n')
    # connect to database
    db['engine'] = create_engine('postgresql+psycopg2://postgres:' + db['passw'] + '@' + db['host'] + '/' + db['name'] + '?port=' + db['port'])
    db['address'] = "host=" + db['host'] + " dbname=" + db['name'] + " user=postgres password='"+ db['passw'] + "' port=" + db['port']
    db['con'] = psycopg2.connect(db['address'])
    logger.info('Database connection established')
    return(db)


############## Query Points ##############
def query_points(db, config):
    '''
    query OSRM for distances between origins and destinations
    '''
    location = config['location']
    # connect to db
    cursor = db['con'].cursor()

    # get list of all origin ids
    sql = "SELECT * FROM block"
    orig_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')

    orig_df['x'] = orig_df.geom.centroid.x
    orig_df['y'] = orig_df.geom.centroid.y
    # drop duplicates
    orig_df.drop('geom',axis=1,inplace=True)
    orig_df.drop_duplicates(inplace=True)
    # set index (different format for different census blocks)
    if location['country'] == 'nz':
        orig_df.sort_values(by=['sa12018_v1'], inplace=True)
        orig_df = orig_df.set_index('sa12018_v1')
    elif location['country'] in ('us','usa'):
        orig_df = orig_df.set_index('geoid10')
        orig_df.sort_values(by=['geoid10'], inplace=True)
    # get list of destination ids
    sql = "SELECT * FROM destinations"
    dest_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
    dest_df = dest_df.set_index('dest_type')
    dest_df = dest_df.loc[config['services']]
    dest_df = dest_df.reset_index()

    dest_df = dest_df.set_index('id')
    dest_df['lon'] = dest_df.geom.centroid.x
    dest_df['lat'] = dest_df.geom.centroid.y
    # list of origxdest pairs
    origxdest = pd.DataFrame(list(itertools.product(orig_df.index, dest_df.index)), columns = ['id_orig', 'id_dest'])
    for metric in config['metric']:
        origxdest['{}'.format(metric)] = None
    origxdest['dest_type'] = len(orig_df)*list(dest_df['dest_type'])
    # df of durations, distances, ids, and co-ordinates
    origxdest = execute_table_query(origxdest, orig_df, dest_df, config)
    return origxdest

############## Parallel Table Query ##############
def execute_table_query(origxdest, orig_df, dest_df, config):
    # Use the table service so as to reduce the amount of requests sent
    # https://github.com/Project-OSRM/osrm-backend/blob/master/docs/http.md#table-service

    batch_limit = 10000
    dest_n = len(dest_df)
    orig_n = len(orig_df)
    orig_per_batch = int(batch_limit/dest_n)
    batch_n = math.ceil(orig_n/orig_per_batch)

    #create query string
    osrm_url = config['OSRM']['host'] + ':' + config['OSRM']['port']
    base_string = osrm_url + "/table/v1/{}/".format(config['transport_mode'])

    # make a string of all the destination coordinates
    dest_string = ""
    dest_df.reset_index(inplace=True, drop=True)
    for j in range(dest_n):
        #now add each dest in the string
        dest_string += str(dest_df['lon'][j]) + "," + str(dest_df['lat'][j]) + ";"
    #remove last semi colon
    dest_string = dest_string[:-1]

    # options string ('?annotations=duration,distance' will give distance and duration)
    if len(config['metric']) == 2:
        options_string_base = '?annotations=duration,distance'
    else:
        options_string_base = '?annotations={}'.format(config['metric'][0]) #'?annotations=duration,distance'
    # loop through the sets of
    orig_sets = [(i, min(i+orig_per_batch, orig_n)) for i in range(0,orig_n,orig_per_batch)]

    # create a list of queries
    query_list = []
    for i in orig_sets:
        # make a string of all the origin coordinates
        orig_string = ""
        orig_ids = range(i[0],i[1])
        for j in orig_ids:
            #now add each dest in the string
            orig_string += str(orig_df.x[j]) + "," + str(orig_df.y[j]) + ";"
        # make a string of the number of the sources
        source_str = '&sources=' + str(list(range(len(orig_ids))))[1:-1].replace(' ','').replace(',',';')
        # make the string for the destinations
        dest_idx_str = '&destinations=' + str(list(range(len(orig_ids), len(orig_ids)+len(dest_df))))[1:-1].replace(' ','').replace(',',';')
        # combine and create the query string
        options_string = options_string_base + source_str + dest_idx_str
        query_string = base_string + orig_string + dest_string + options_string
        # append to list of queries
        query_list.append(query_string)
    # # Table Query OSRM in parallel
    #define cpu usage
    num_workers = np.int(mp.cpu_count() * config['par_frac'])
    #gets list of tuples which contain 1list of distances and 1list
    logger.info('Querying the origin-destination pairs:')
    results = Parallel(n_jobs=num_workers)(delayed(req)(query_string, config) for query_string in tqdm(query_list))
    logger.info('Querying complete.')
    # get the results in the right format
    if len(config['metric']) == 2:
        dists = [l for orig in results for l in orig[0]]
        durs = [l for orig in results for l in orig[1]]
        origxdest['distance'] = dists
        origxdest['duration'] = durs
    else:
        formed_results = [result for query in results for result in query]
        origxdest['{}'.format(config['metric'][0])] = formed_results
    return(origxdest)

############## Read JSON ##############
def req(query_string, config):
    response = requests.get(query_string).json()
    if len(config['metric']) == 2:
        temp_dist = [item for sublist in response['distances'] for item in sublist]
        temp_dur = [item for sublist in response['durations'] for item in sublist]
        return temp_dist, temp_dur
    else:
        return [item for sublist in response['{}s'.format(config['metric'][0])] for item in sublist]


############## Create Destination Table in SQL ##############
def create_dest_table(db, config):
    '''
    create a table with the destinations
    '''
    # db connections
    con = db['con']
    engine = db['engine']
    # destinations and locations
    types = config['services']
    # projection
    projection = config['set_up']['projection']
    # import the csv's
    gdf = gpd.GeoDataFrame()
    count = 0
    for dest_type in types:
        file = config['set_up']['destination_file_directory'][count]
        df_type = gpd.read_file(r'{}'.format(file))
        # df_type = pd.read_csv('data/destinations/' + dest_type + '_FL.csv', encoding = "ISO-8859-1", usecols = ['id','name','lat','lon'])
        df_type['dest_type'] = dest_type
        df_type = df_type.to_crs("EPSG:{}".format(projection))
        gdf = gdf.append(df_type)
        count += 1
    # set a unique id for each destination
    gdf['id'] = range(len(gdf))
    # prepare for sql
    gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=projection))
    #drop all columns except id, dest_type, and geom
    gdf = gdf[['id','dest_type','geom']]
    # set index
    gdf.set_index(['id','dest_type'])
    # export to sql
    gdf.to_sql('destinations', engine, if_exists='replace', dtype={'geom': Geometry('POINT', srid= projection)})
    # update indices
    cursor = con.cursor()
    queries = ['CREATE INDEX "destinations_id" ON destinations ("id");',
            'CREATE INDEX "destinations_type" ON destinations ("dest_type");']
    for q in queries:
        cursor.execute(q)
    # commit to db
    con.commit()

############## Create Origin/Block Table in SQL ##############
def create_origin_table(db, config):
    '''
    create a table with the origin blocks
    '''
    # db connections
    con = db['con']
    engine = db['engine']
    # projection
    projection = config['set_up']['projection']
    # import the csv's
    file = config['set_up']['origin_file_directory']
    gdf = gpd.read_file(r'{}'.format(file))
    gdf = gdf.to_crs("EPSG:{}".format(projection))
    # prepare for sql
    gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=projection))
    # export to sql
    gdf.to_sql('block_test', engine, if_exists='replace', dtype={'geom': Geometry('POLYGON', srid=projection)})
    # commit to db
    con.commit()

############## Save to SQL ##############
def write_to_postgres(df, db, indices=True):
    ''' quickly write to a postgres database
        from https://stackoverflow.com/a/47984180/5890574'''
    table_name = db['table_name']
    logger.info('Writing data to SQL')
    df.head(0).to_sql(table_name, db['engine'], if_exists='replace',index=False) #truncates the table
    conn = db['engine'].raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    cur.copy_from(output, table_name, null="") # null values become ''
    logger.info('Distances written successfully to SQL as "{}"'.format(table_name))
    # update indices
    logger.info('Updating indices on SQL')
    if indices == True:
        if table_name == db['table_name']:
            queries = [
                        'CREATE INDEX "{0}_dest_id" ON {0} ("id_dest");'.format(db['table_name']),
                        'CREATE INDEX "{0}_orig_id" ON {0} ("id_orig");'.format(db['table_name'])
                        ]
        for q in queries:
            cur.execute(q)
    conn.commit()


if __name__ == '__main__':
    main()
