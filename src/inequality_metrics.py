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
epsilon = 0.5
compare_city = False
states = ['wa', 'md','fl', 'co', 'mi', 'la', 'ga', 'or', 'tx', 'il']
compare_race = False
races = ['all', 'white', 'non_white', 'black', 'american_indian', 'asian', 'hispanic'] #Black and african american, indiand and native alaskan, hispanic and latino
file_name = 'test_results'

import utils
from config import *


def main():
    data, kapa = calc_kapa()
    gini_inds = []
    at_adj_inds = []
    at_inds = []
    kp_inds = []
    kp_edes = []
    at_adj_edes = []
    at_edes = []
    dist_means = []
    dist_maxs = []
    dist_stds = []
    dist_covs = []
    kapas = []
    betas = []
    epsilons = []
    states_ = []

    for state in states:
        df = data['{}_data'.format(state)]
        gini = get_gini(df)
        gini_inds.append(gini)

        at_adj_ind, at_adj_ede = get_at_adj(df)
        at_adj_inds.append(at_adj_ind)
        at_adj_edes.append(at_adj_ede)

        at_ind, at_ede = get_at(df)
        at_inds.append(at_ind)
        at_edes.append(at_ede)

        kp_ind, kp_ede = get_kp(df, kapa)
        kp_inds.append(kp_ind)
        kp_edes.append(kp_ede)

        mean, max, std, cov = get_stats(df)
        dist_means.append(mean)
        dist_maxs.append(max)
        dist_stds.append(std)
        dist_covs.append(cov)

        kapas.append(kapa)
        betas.append(beta)
        epsilons.append(epsilon)

        states_.append(state)
    results = pd.DataFrame(list(zip(states_, kapas, betas, epsilons, kp_edes, at_edes, at_adj_edes, kp_inds, at_inds, at_adj_inds, gini_inds, dist_means, dist_maxs, dist_stds, dist_covs)), columns=['State', 'Kapa', 'Beta', 'Epsilon', 'Kolm Pollock EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm Pollock Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation'])
    results.to_csv(r'/homedirs/man112/access_inequality_index/data/results/{}.csv'.format(file_name))


def calc_kapa():
    #Makes a dictionary of nearest dist and demo
    dist = {}
    for state in states:
        db, context = cfg_init(state)
        cursor = db['con'].cursor()
        sql = 'SELECT * FROM distxdem'
        dist["{}_df".format(state)] = pd.read_sql(sql, db["con"])
        db['con'].close()

    #Sorts the dfs for each state and gives population columns
    data = {}
    kapa_data = []
    for state in states:
        df = dist['{}_df'.format(state)]
        df = df.dropna()
        data['{}_data'.format(state)] = df
        count = 0
        for i in df['distance']/1000:
            for pop in range(int(df['H7X001'].iloc[count])):
                kapa_data.append(i)
            count += 1

    x_sum = 0
    x_sq_sum = 0
    for i in kapa_data:
        x_sum += i
        x_sq_sum += i**2
    kapa = beta*(x_sum/x_sq_sum)
    return(data, kapa)

def get_gini(df):
    dist_tot = df['distance'].sum()
    pop_tot = df['H7X001'].sum()
    df = df.sort_values(by='distance')
    df['pop_perc'] = df['H7X001'].cumsum()/pop_tot*100
    df['dist_perc'] = df['distance'].cumsum()/dist_tot*100
    area_tot = simps(np.arange(0,101,1), dx=1)
    area_real = simps(df['dist_perc'], df['pop_perc'])
    area_diff = area_tot - area_real
    gini = area_diff/area_tot
    gini = round(gini, 3)
    gini = 1
    return(gini)

def get_at_adj(df):
    at_sum = 0
    count = 0
    N = df['H7X001'].sum()
    x_mean = np.average(df['distance'], weights = df['H7X001'])/1000
    for i in df['distance']/1000:
        at_sum += (i**(1-beta))*df['H7X001'].iloc[count]
        count += 1
    at_ede = (at_sum/N)**(1/(1-beta))
    at_ind = (at_ede/x_mean)-1
    return(at_ind, at_ede)

def get_at(df):
    at_sum = 0
    N = df['H7X001'].sum()
    x_mean = np.average(df['distance'], weights = df['H7X001'])/1000
    count = 0
    for i in df['distance']/1000:
        i = 1/i
        at_sum += (i**(1-epsilon))*df['H7X001'].iloc[count]
        count += 1
    at_ede = (at_sum/N)**(1/(1-epsilon))
    at_ind = 1 - (at_ede/x_mean)
    return(at_ind, at_ede)

def get_kp(df, kapa):
    N = df['H7X001'].sum()
    x_mean = np.average(df['distance'], weights = df['H7X001'])/1000
    sum_ede = 0
    sum_ii = 0
    count = 0
    for x_n in df['distance']/1000:
        sum_ede += np.exp(-kapa*x_n)*df['H7X001'].iloc[count]
        sum_ii += np.exp(-kapa*(x_n-x_mean))*df['H7X001'].iloc[count]
        count += 1
    kp_ede = (-1/kapa)*np.log(sum_ede/N)
    kp_ind = -(1/kapa)*np.log(sum_ii/N)
    return(kp_ind, kp_ede)

def get_stats(df):
    pop_total = df['H7X001'].sum()
    df = df.sort_values(by='distance')
    hist_data = []
    count =0
    for i in df['distance']/1000:
        for pop in range(int(df['H7X001'].iloc[count])):
            hist_data.append(i)
        count += 1
    mean = np.mean(hist_data)
    max = np.max(hist_data)
    std = np.std(hist_data)
    cov = std/mean
    return(mean, max, std, cov)


if __name__ == '__main__':
    main()
