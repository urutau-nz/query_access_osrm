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
    dfs = []
    kapa_data = []
    d= {}
    for state in states:
        db, context = cfg_init(state)
        cursor = db['con'].cursor()
        sql = 'SELECT * FROM nearest_dist'
        d["{}_df".format(state)] = pd.read_sql(sql, db["con"])
        sql = 'SELECT * FROM demograph'
        d["{}_demo".format(state)] = pd.read_sql(sql, db['con'])
        db['con'].close()
    print(type(d))
    for df in d:
        dfs.append(df)
    print(dfs)
        #exec(f'{state} = {state}.sort_values(by="geoid10")')
        #exec(f'{state}_demo = {state}.sort_values(by="geoid10")')
        #exec(f'{state}["pop_all"] = {state}_demo["H7X001"]')
        #exec(f'{state}["pop_white"] = {state}_demo["H7X002"]')
        #exec(f'{state}["pop_non_white"] = {state}_demo["H7X001"] - {state}_demo["H7X002"]')
        #exec(f'{state}["pop_black"] = {state}_demo["H7X003"]')
        #exec(f'{state}["pop_american_indian"] = {state}_demo["H7X004"]')
        #exec(f'{state}["pop_asian"] = {state}_demo["H7X005"]')
        #exec(f'{state}["pop_hispanic"] = {state}_demo["H7Y003"]')
        #for distance in {state}

calc_kapa()
