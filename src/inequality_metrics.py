'''
The goal of this script is to do any of the following:
For supermarkets in a given city:
    1. Calculate the EDEs and Indices
    2. Plot a population weight Histogram with summary statistics
    3. Plot a gini curve
    4. Plot a CDF
    5. Return a CSV file with all EDEs, Indices, and Summary statistics
For a list of races/ethnicities within a given city:
    1. Calculate the EDEs and Indices for each race
    2. Plot a population weight Histogram with summary statistics for each race
    3. Plot a gini curve for each race
    4. Plot a CDF for each race
    5. Return a CSV file with all EDEs, Indices, and Summary statistics
For a list of cities:
    1. Calculate the EDEs and Indices
    2. Plot a population weight Histogram with summary statistics
    3. Plot a gini curve
    4. Plot a CDF
    5. Return a CSV file with all EDEs, Indices, and Summary statistics
'''

# User defined variables
# Will compare the
beta = -0.5
compare_city = False
states = ['wa', 'md']#,'fl', 'co', 'mi', 'la', 'ga', 'or', 'tx', 'il']
compare_race = False
races = ['all', 'white', 'non_white', 'black', 'american_indian', 'asian', 'hispanic'] #Black and african american, indiand and native alaskan, hispanic and latino
file_name = ''

import utils
from config import *


def main():
    kapa = calc_kapa()


def calc_kapa():
    #Makes a dictionary of nearest dist and demo
    dist = {}
    demo = {}
    for state in states:
        db, context = cfg_init(state)
        cursor = db['con'].cursor()
        sql = 'SELECT * FROM nearest_dist'
        dist["{}_df".format(state)] = pd.read_sql(sql, db["con"])
        sql = 'SELECT * FROM demograph'
        demo["{}_demo".format(state)] = pd.read_sql(sql, db['con'])
        db['con'].close()

    #Sorts the dfs for each state and gives population columns
    data = {}
    kapa_data = []
    for state in states:
        df = dist['{}_df'.format(state)]
        dem = demo['{}_demo'.format(state)]
        df = df.sort_values(by='id_orig')
        dem = dem.sort_values(by='geoid10')
        df = df.dropna()
        dem = dem.dropna()
        df = df.loc[df['distance'] != 0]
        dem = dem.loc[dem['H7X001'] !=0]
        df['pop_all'] = dem['H7X001']
        df['pop_white'] = dem['H7X002']
        df['pop_non_white'] = dem['H7X001'] - dem['H7X002']
        df['pop_black'] = dem['H7X003']
        df['pop_americian_indian'] = dem['H7X004']
        df['pop_asian'] = dem['H7X005']
        #df['hispanic'] = dem['H7Y003']
        data['{}_data'.format(state)] = df

        count = 0
        for i in df['distance']/1000:
            for pop in range(int(df['pop_all'].iloc[count])):
                kapa_data.append(i)
            count += 1

    x_sum = 0
    x_sq_sum = 0
    for i in kapa_data:
        x_sum += i
        x_sq_sum += i**2
    kapa = beta*(x_sum/x_sq_sum)

    print(data)
    print(kapa)

    #print(dist['md_df'], demo['md_demo'])

calc_kapa()
