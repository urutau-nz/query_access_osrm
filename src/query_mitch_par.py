'''
Init the database
Query origins to dests in OSRM
'''
# user defined variables
state = input('State: ')
par = True
par_frac = 0.9

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
    origxdest['duration'] = None

    # df of durations, distances, ids, and co-ordinates
    origxdest = execute_table_query(origxdest, orig_df, dest_df)

    # add df to sql
    logger.info('Writing data to SQL')
    origxdest.to_sql('distance_duration', con=db['engine'], if_exists='replace', index=False, dtype={"distance":Float(), "duration":Float(), 'id_dest':Integer()})
    logger.info('Distances written successfully to SQL')
    logger.info('Updating indices on SQL')
    # update indices
    queries = ['CREATE INDEX "dest_idx" ON distance_duration ("id_dest");','CREATE INDEX "orig_idx" ON distance_duration ("id_orig");']
    for q in queries:
        cursor.execute(q)

    # commit to db
    db['con'].commit()
    logger.info('Query Complete')


def execute_table_query(origxdest, orig_df, dest_df):
    #Use the table service so as to reduce the amount of requests sent
    # https://github.com/Project-OSRM/osrm-backend/blob/master/docs/http.md#table-service

    #init list for destination & origin co-ords
    #dest_locs = []
    #orig_locs = []

    #create query string
    # the query looks like this: '{}/route/v1/driving/{},{};{},{}?overview=false'.format(osrm_url, lon_o, lat_o, lon_d, lat_d)
    base_string = context['osrm_url'] + "/table/v1/driving/"
    dest_string = ""
    #make queries for each orig, this single table query has all destinations
    for j in range(len(dest_df)):
        #now add each dest in the string
        dest_string += str(dest_df['lon'][j]) + "," + str(dest_df['lat'][j]) + ";"
        #get list of destination co-ordinates
        #dest_locs.append(str(dest_df['lon'][j]) + "," + str(dest_df['lat'][j]))

    #remove last semi colon
    dest_string = dest_string[:-1]
    #fill column of destination co-ords
    #origxdest['dest_loc'] = len(orig_df)*dest_locs
    #init list for query objects
    query_list = []
    #create the query strings
    for i in range(len(orig_df)):
        #list of orig co-ords
        #temp_orig_locs = len(dest_df)*[str(orig_df.x[i]) + "," + str(orig_df.y[i])]
        #orig_locs = orig_locs + temp_orig_locs
        #make query string
        temp_query_wrapper = QueryWrapper(base_string, orig_df.x[i], orig_df.y[i])
        #add orig in position 0 of the query string
        temp_query_wrapper.query_string += str(orig_df.x[i]) + "," + str(orig_df.y[i]) + ";"
        #add destinations to query too
        temp_query_wrapper.query_string += dest_string
        #returns matrix of durations in seconds and distances in meters. Sources=0 indicates that the orig co-ord is in index 0
        temp_query_wrapper.query_string += "?annotations=duration,distance&sources=0"
        #append query string
        query_list.append(temp_query_wrapper)

    #fill column with orig co-ords
    #origxdest['orig_loc'] = orig_locs
    #code.interact(local=locals())
    # Table Query OSRM in parallel
    if par == True:
        #define cpu usage
        num_workers = np.int(mp.cpu_count() * par_frac)
        #gets list of tuples which contain 1list of distances and 1list
        results = Parallel(n_jobs=num_workers)(delayed(req)(query_wrapper) for query_wrapper in tqdm(query_list))
    code.interact(local=locals())
    dists = []
    durs = []
    for orig in results:
        dists = dists + orig[0]
        durs = durs + orig[1]
    origxdest['distance'] = dists
    origxdest['duration'] = durs
    return(origxdest)

def req(query_wrapper):
    response = requests.get(query_wrapper.query_string).json()
    dists = response['distances'][0][1:]
    durs = response['durations'][0][1:]
    locs = []
    for i in response['destinations']:
        locs.append(i['location'])
    df = pd.DataFrame()
    df['dest_loc'] = locs[1:]
    df['distance'] = dists
    df['duration'] = durs
    df['orig_y'] = response['sources'][0]['location'][1]
    df['orig_x'] = response['sources'][0]['location'][0]
    return df

class QueryWrapper:

    def __init__(self, query_string, orig_loc_x, orig_loc_y):
        self.query_string = query_string
        self.orig_loc_x = orig_loc_x
        self.orig_loc_y = orig_loc_y

if __name__ == "__main__":
    logger.info('query.py code invoked')
    main(db, context)
