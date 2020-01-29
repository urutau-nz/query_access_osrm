# user defined variables
state = input('State: ')
from config import *
db, context = cfg_init(state)


def import_csv(db):
    '''
    import a csv into the postgres db
    '''
    if state=='md':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '510'
    elif state == 'wa':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '033'
    elif state == 'nc':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '129'
    elif state == 'il':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '031'
    elif state == 'tx':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '201'
    elif state == 'or':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '051'
    elif state == 'ga':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '121'
    elif state == 'la':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '071'
    elif state == 'mi':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '163'
    elif state == 'co':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '031'
    elif state == 'fl':
        file_name = '/homedirs/man112/access_inequality_index/data/usa/{}/{}/demo/demo.csv'.format(state, context['city_code'])
        county = '086'
    #
    table_name = 'demograph'

    # import distances
    dist = pd.read_sql('SELECT id_orig, distance FROM nearest_dist', db['con'])
    dist = dist.loc[dist['distance']!=0]
    dist['geoid10'] = dist['id_orig']
    # import demographic
    demo = pd.read_csv(file_name, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLOCKA':str, 'H7X001':int, 'H7X002':int, 'H7X003':int, 'H7X004':int, 'H7X005':int, 'H7Y003':int})
    demo = demo.loc[demo['H7X001']!=0] # remove zero pop blocks
    demo['geoid10'] = demo['geoid10'] = demo['STATEA'] + demo['COUNTYA'] + demo['TRACTA'] + demo['BLOCKA']

    # join the dataframes
    dem_cols = ['geoid10','H7X001', 'H7X002', 'H7X003', 'H7X004', 'H7X005', 'H7Y003']
    distxdem = pd.merge(dist[['geoid10','distance']], demo[dem_cols], on='geoid10', how='inner')

    # upload to sql
    distxdem.to_sql('distxdem', db['engine'])
    cursor = db['con'].cursor()
    # commit
    db['con'].commit()


if __name__ == '__main__':
    import_csv(db)
