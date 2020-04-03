'''
Init the database
Query origins to dests in OSRM
'''
# user defined variables
state = input('State: ')
query_mode = input("Choose query mode [route, table]: ")
par = True
par_frac = 0.8

import utils
from config import *
db, context = cfg_init(state)
logger = logging.getLogger(__name__)
import os.path
import osgeo.ogr
import shapely
from geoalchemy2 import Geometry, WKTElement
import requests
from sqlalchemy.types import Float, Integer
if par == True:
    import multiprocessing as mp
    from joblib import Parallel, delayed
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry

def main(db, context):
    '''
    set up the db tables I need for the querying
    '''

    # init the destination tables
    #create_dest_table(db)

    # query the distances
    query_points(db, context)

    # close the connection
    db['con'].close()
    logger.info('Database connection closed')

    # email completion notification
    #utils.send_email(body='Querying {} complete'.format(context['city']))


def create_dest_table(db):
    '''
    create a table with the destinations
    '''
    # db connections
    con = db['con']
    engine = db['engine']
    # destinations and locations
    types = ['supermarket', 'hospital']
    # import the csv's
    gdf = gpd.GeoDataFrame()
    for dest_type in types:
        files = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/{}/{}_{}.shp'.format(state, context['city_code'], dest_type, state, dest_type)
        df_type = gpd.read_file('{}'.format(files))
        # df_type = pd.read_csv('data/destinations/' + dest_type + '_FL.csv', encoding = "ISO-8859-1", usecols = ['id','name','lat','lon'])
        if df_type.crs['init'] != 'epsg:4269':
            # project into lat lon
            df_type = df_type.to_crs({'init':'epsg:4269'})
        df_type['dest_type'] = dest_type
        gdf = gdf.append(df_type)

    # set a unique id for each destination
    gdf['id'] = range(len(gdf))
    # prepare for sql
    gdf['geom'] = gdf['geometry'].apply(lambda x: WKTElement(x.wkt, srid=4269))
    #drop all columns except id, dest_type, and geom
    gdf = gdf[['id','dest_type','geom']]
    # set index
    gdf.set_index(['id','dest_type'], inplace=True)

    # export to sql
    gdf.to_sql('destinations', engine, dtype={'geom': Geometry('POINT', srid= 4269)})

    # update indices
    cursor = con.cursor()
    queries = ['CREATE INDEX "dest_id" ON destinations ("id");',
            'CREATE INDEX "dest_type" ON destinations ("dest_type");']
    for q in queries:
        cursor.execute(q)

    # commit to db
    con.commit()


def query_points(db, context):
    '''
    query OSRM for distances between origins and destinations
    '''
    # connect to db
    cursor = db['con'].cursor()

    # get list of all origin ids
    sql = "SELECT * FROM block"
    orig_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
    orig_df['x'] = orig_df.geom.centroid.x
    orig_df['y'] = orig_df.geom.centroid.y
    print(orig_df.x)
    # drop duplicates
    orig_df.drop('geom',axis=1,inplace=True)
    orig_df.drop_duplicates(inplace=True)
    # set index
    orig_df = orig_df.set_index('geoid10')

    # get list of destination ids
    sql = "SELECT * FROM destinations"
    dest_df = gpd.GeoDataFrame.from_postgis(sql, db['con'], geom_col='geom')
    dest_df = dest_df.set_index('id')
    dest_df['lon'] = dest_df.geom.centroid.x
    dest_df['lat'] = dest_df.geom.centroid.y

    # list of origxdest pairs
    origxdest = pd.DataFrame(list(itertools.product(orig_df.index, dest_df.index)), columns = ['id_orig','id_dest'])
    origxdest['distance'] = None

    #Use the table service so as to send only one request and a reply with all of the data
    #Probably stick with MLD as pre-proccesing wont do much when changing things as CD only gets faster with good pre-processing
    # https://github.com/Project-OSRM/osrm-backend/blob/master/docs/http.md#table-service


    if(query_mode == "table"):
        origxdest = execute_table_query(origxdest, orig_df, dest_df)
    elif(query_mode == "route"):
        origxdest = execute_route_query(origxdest, orig_df, dest_df)
    else:
        origxdest = execute_route_query(origxdest, orig_df, dest_df)
    # add df to sql
    logger.info('Writing data to SQL')
    origxdest.to_sql('distance', con=db['engine'], if_exists='replace', index=False, dtype={"distance":Float(), 'id_dest':Integer()})
    # update indices
    queries = ['CREATE INDEX "dest_idx" ON distance ("id_dest");',
            'CREATE INDEX "orig_idx" ON distance ("id_orig");']
    for q in queries:
        cursor.execute(q)

    # commit to db
    db['con'].commit()
    logger.info('Distances written successfully to SQL')


def single_query(query):
    '''
    this is for if we want it parallel
    query a value and add to the table
    '''
    # query
    # dist = requests.get(query).json()['routes'][0]['legs'][0]['distance']
    dist = requests_retry_session(retries=100, backoff_factor=0.01, status_forcelist=(500, 502, 504), session=None).get(query).json()['routes'][0]['legs'][0]['distance']
    # dist = r.json()['routes'][0]['legs'][0]['distance']
    return(dist)


def requests_retry_session(retries=0, backoff_factor=0.1, status_forcelist=(500, 502, 504), session=None):
    '''
    When par ==True, issues with connecting to the docker, can change the retries to keep trying to connect
    '''
    session = session or requests.Session()
    retry = Retry(total=retries, read=retries, connect=retries, backoff_factor=backoff_factor, status_forcelist=status_forcelist)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def add_column_demograph(con):
    '''
    Add a useful geoid10 column to join data with
    '''
    queries = ['ALTER TABLE demograph ADD COLUMN geoid10 CHAR(15)',
                '']
def execute_route_query(origxdest, orig_df, dest_df):
    # build query list:
    query_0 = np.full(fill_value = context['osrm_url'] + '/route/v1/driving/', shape=origxdest.shape[0], dtype = object)
    # the query looks like this: '{}/route/v1/driving/{},{};{},{}?overview=false'.format(osrm_url, lon_o, lat_o, lon_d, lat_d)
    queries = query_0 + np.array(orig_df.loc[origxdest['id_orig'].values]['x'].values, dtype = str) + ',' + np.array(orig_df.loc[origxdest['id_orig'].values]['y'].values, dtype = str) + ';' + np.array(dest_df.loc[origxdest['id_dest'].values]['lon'].values, dtype = str) + ',' + np.array(dest_df.loc[origxdest['id_dest'].values]['lat'].values, dtype = str) + '?overview=false'
    ###
    # loop through the queries
    ###
    logger.info('Beginning to query {}'.format(context['city']))
    total_len = len(queries)
    if par == True:
        # Query OSRM in parallel
        num_workers = np.int(mp.cpu_count() * par_frac)
        distances = Parallel(n_jobs=num_workers)(delayed(single_query)(query) for query in tqdm(queries))
        # input distance into df
        origxdest['distance'] = distances
    else:


        for index, query in enumerate(tqdm(queries)):
            # single query
            r = requests.get(query)
            # input distance into df
            origxdest.loc[index,'distance'] = r.json()['routes'][0]['legs'][0]['distance']
    logger.info('Querying complete')

    return origxdest


def execute_table_query(origxdest, orig_df, dest_df):
    #here we want a for loop of string comp to build the query with the table instead of creating shitloads of induvidual queries
    print(dest_df['lon'])
    print(dest_df[12])
    iterator = 0
    destination_string = "&destinations="
    source_string = "?sources="
    base_string = context['osrm_url'] + "/table/v1/driving/"
    for i in range(len(origxdest['id_orig'])) :
        base_string += str(orig_df.x[i]) + "," + str(orig_df.y[i]) + ";"
        source_string += str(iterator) + ";"
        iterator += 1
        base_string += str(dest_df.lon[i]) + "," + str(dest_df.lat[i]) + ";"
        #base_string += origxdest["id_dest"].values['x'][i].value + "," + origxdest["id_dest"].values['y'][i].value + ";"
        destination_string += str(iterator) + ";"
        iterator += 1


    #removes the semicolon at the end
    destination_string = destination_string[:-1]
    source_string = source_string[:-1]
    base_string = base_string[:-1]

    query_string = base_string + source_string + destination_string + "&annotation=distance"

    #hopefully not too big of a data request
    r = requests.get(query_string)
    #need to process r here to get the required info
    for index, pair in origxdest:
        origxdest.loc[index, 'distance'] = r.json()["distance"][index]

    return origxdest




if __name__ == "__main__":
    logger.info('query.py code invoked')
    main(db, context)
