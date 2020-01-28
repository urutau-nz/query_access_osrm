'''
General functions that support the project
- import_csv for csv -> postgres db
-
'''
# user defined variables
state = input('State: ')
from config import *
db, context = cfg_init(state)

import yagmail


def send_email(body):
    # send an email

    receiver = "man112@uclive.ac.nz"
    # filename = "document.pdf"

    yag = yagmail.SMTP('toms.scrapers',open('pass_email.txt', 'r').read().strip('\n'))
    yag.send(
        to=receiver,
        subject="Your code notification",
        contents=body,
        # attachments=filename,
    )


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
    # add csv to nc.demograph
    df = pd.read_csv(file_name, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLOCKA':str, 'H7X001':int, 'H7X002':int, 'H7X003':int, 'H7X004':int, 'H7X005':int, 'H7Y003':int})
    df = df[df.COUNTYA==county]
    df['geoid10'] = df['STATEA'] + df['COUNTYA'] + df['TRACTA'] + df['BLOCKA']
    df.to_sql(table_name, db['engine'])
    # add the table indices

    cursor = db['con'].cursor()
    queries = ['CREATE INDEX "geoid10" ON demograph ("geoid10");',
            'CREATE INDEX "id" ON demograph ("BLOCKA");']
    for q in queries:
        cursor.execute(q)
    # commit
    db['con'].commit()


if __name__ == '__main__':
    import_csv(db)
