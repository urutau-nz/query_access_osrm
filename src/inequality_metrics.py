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
states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'il', 'wa', 'tx']
compare_race = False
races = ['all', 'white', 'non_white', 'black', 'american_indian', 'asian', 'hispanic'] #Black and african american, indiand and native alaskan, hispanic and latino
file_name = 'test_results'

import utils
from config import *


def main():
    data, kapa, city = calc_kapa()
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

    plot_gini(data)
    plot_hist(data)
    #plot_cdf(data)

    results = pd.DataFrame(list(zip(states_, city, kapas, betas, epsilons, kp_edes, at_edes, at_adj_edes, kp_inds, at_inds, at_adj_inds, gini_inds, dist_means, dist_maxs, dist_stds, dist_covs)), columns=['State','City', 'Kapa', 'Beta', 'Epsilon', 'Kolm Pollock EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm Pollock Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation'])
    results.to_csv(r'/homedirs/man112/access_inequality_index/data/results/{}.csv'.format(file_name))


def calc_kapa():
    #Makes a dictionary of nearest dist and demo
    dist = {}
    city = []
    for state in states:
        db, context = cfg_init(state)
        cursor = db['con'].cursor()
        sql = 'SELECT * FROM distxdem'
        dist["{}_df".format(state)] = pd.read_sql(sql, db["con"])
        db['con'].close()
        city.append(context['city'])

    #Sorts the dfs for each state and gives population columns
    data = {}
    kapa_data = []
    for state in states:
        df = dist['{}_df'.format(state)]
        df = df.loc[df['distance'] !=0]
        df = df.loc[df['H7X001'] !=0]
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
    return(data, kapa, city)

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
    #gini = 1
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

def plot_gini(data):
    for state in states:
        df = data['{}_data'.format(state)]
        pop_tot = df.H7X001.sum()
        dist_tot = df.distance.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df.H7X001.cumsum()/pop_tot*100
        df['dist_perc'] = df.distance.cumsum()/dist_tot*100
        plt.plot(df.pop_perc, df.dist_perc, label=state)
    plt.plot(np.arange(0,101,1), np.arange(0, 101, 1), '--', color='black', lw=0.5, label = 'Perfect Equality Line')
    plt.xlabel('% Residents')
    # xlabel
    plt.ylabel('% Distance')
    plt.xlim([0,None])
    plt.ylim([0,None])
    plt.title('Gini Curve'.format(loc='center'))
    plt.legend(loc='best')
    #Save figrue
    fig_out = '/homedirs/man112/access_inequality_index/data/results/GINI_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    plt.clf()

def plot_hist(data):
    fig, axes = plt.subplots(ncols=2,nrows=5, sharex=True, sharey=False, gridspec_kw={'hspace':0.5})
    for state, ax in zip(states, axes.flat):
        df = data['{}_data'.format(state)]
        pop_tot = df.H7X001.sum()
        df = df.sort_values(by='distance')
        hist_data = []
        count = 0
        for i in tqdm((df.distance)/1000):
            for pop in range(df.H7X001.iloc[count]):
                hist_data.append(i)
        sns.distplot(hist_data, hist = True, kde = True, bins = int(100), label = state, ax=ax, color=random.choice(['red','blue','green','yellow','orange','purple', 'pink']), kde_kws={'color':'black'})

    plt.xlim([0,20])
    plt.ylim([0,None])

    fig_out = '/homedirs/man112/access_inequality_index/data/results/HIST_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, format='pdf')#, bbox_inches='tight')
    plt.clf()

if __name__ == '__main__':
    main()

    plt.xlim([0,20])
    plt.ylim([0,None])

    fig_out = '/homedirs/man112/Project11/data/processed/figures/food_des/{}_HIST.pdf'.format(fig_name)
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, format='pdf')#, bbox_inches='tight')
    plt.clf()



if __name__ == '__main__':
    main()
