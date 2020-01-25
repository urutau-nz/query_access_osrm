'''
General functions that support the project
- import_csv for csv -> postgres db
-
'''
# user defined variables
state = 'wa'
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
    # Might be wrong file paths
    if state=='md':
        file_name = 'data/bal/block/nhgis0033_csv/nhgis0033_ds172_2010_block.csv'
        county = '510'
    elif state == 'wa':
        file_name = 'data/sea/block/nhgis0034_csv/nhgis0034_ds172_2010_block.csv'
        county = '033'
    elif state == 'nc':
        file_name = 'data/wil/block/nhgis0031_csv/nhgis0031_ds172_2010_block.csv'
        county = '129'
    #
    table_name = 'demograph'
    # add csv to nc.demograph
    df = pd.read_csv(file_name, dtype = {'STATEA':str, 'COUNTYA':str,'TRACTA':str,'BLOCKA':str, 'H7X001':int, 'H7X002':int, 'H7X003':int, 'H7X004':int})
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
