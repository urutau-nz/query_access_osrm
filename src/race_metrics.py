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

kapa = -0.170477678 #This should be equal to kapa used for intercity comparisons
states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'il', 'wa', 'tx']
state = input('State: ')
compare_race = False
race_labels = ['all', 'white', 'black', 'american_indian', 'asian', 'hispanic'] #Black and african american, indiand and native alaskan, hispanic and latino
races = ['HX7001', 'HX7002', 'H7X003', 'H7X004', 'H7X005', 'H7Y003']

import utils
from config import *
db, context = cfg_init(state)
cursor = db['con'].cursor()
file_name = '{}_race_results'.format(context['city'])

def main():
    df = get_df()
    gini_inds, at_adj_inds, at_inds, kp_inds, kp_edes, at_adj_edes = [], [], [], [], [], []
    at_edes, dist_means, dist_maxs, dist_stds, dist_covs = [], [], [], [], []
    kapas, betas, epsilons, states_ = [], [], [], []
    for race in races:
        gini = get_gini(df, race)
        gini_inds.append(gini)

        at_adj_ind, at_adj_ede = get_at_adj(df, race)
        at_adj_inds.append(at_adj_ind)
        at_adj_edes.append(at_adj_ede)

        at_ind, at_ede = get_at(df, race)
        at_inds.append(at_ind)
        at_edes.append(at_ede)

        kp_ind, kp_ede = get_kp(df, kapa, race)
        kp_inds.append(kp_ind)
        kp_edes.append(kp_ede)

        mean, max, std, cov = get_stats(df, race)
        dist_means.append(mean)
        dist_maxs.append(max)
        dist_stds.append(std)
        dist_covs.append(cov)

        kapas.append(kapa)
        betas.append(beta)
        epsilons.append(epsilon)

        states_.append(state)

    plot_gini(df)
    plot_hist(df)
    plot_cdf(df)

    results = pd.DataFrame(list(zip(states_, city, races, kapas, betas, epsilons, kp_edes, at_edes, at_adj_edes, kp_inds, at_inds, at_adj_inds, gini_inds, dist_means, dist_maxs, dist_stds, dist_covs)), columns=['State', 'City', 'Race','Kapa', 'Beta', 'Epsilon', 'Kolm Pollock EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm Pollock Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation'])
    results.to_csv(r'/homedirs/man112/access_inequality_index/data/results/{}.csv'.format(file_name))


def get_df():
    #Makes a dictionary of nearest dist and demo
    sql = 'SELECT * FROM distxdem'
    df = pd.read_sql(sql, db["con"])
    db['con'].close()
    city = context['city']

    #Sorts the dfs for each state and gives population columns
    kapa_data = []
    df = df.loc[df['distance'] !=0]
    df = df.loc[df[race] !=0]
    df = df.dropna()
    return(df)

def get_gini(df, race):
    dist_tot = df['distance'].sum()
    pop_tot = df[race].sum()
    df = df.sort_values(by='distance')
    df['pop_perc'] = df[race].cumsum()/pop_tot*100
    df['dist_perc'] = df['distance'].cumsum()/dist_tot*100
    area_tot = simps(np.arange(0,101,1), dx=1)
    area_real = simps(df['dist_perc'], df['pop_perc'])
    area_diff = area_tot - area_real
    gini = area_diff/area_tot
    gini = round(gini, 3)
    #gini = 1
    return(gini)

def get_at_adj(df, race):
    at_sum = 0
    count = 0
    N = df[race].sum()
    x_mean = np.average(df['distance'], weights = df[race])/1000
    for i in df['distance']/1000:
        at_sum += (i**(1-beta))*df[race].iloc[count]
        count += 1
    at_ede = (at_sum/N)**(1/(1-beta))
    at_ind = (at_ede/x_mean)-1
    return(at_ind, at_ede)

def get_at(df, race):
    at_sum = 0
    N = df[race].sum()
    x_mean = np.average(df['distance'], weights = df[race])/1000
    count = 0
    for i in df['distance']/1000:
        i = 1/i
        at_sum += (i**(1-epsilon))*df[race].iloc[count]
        count += 1
    at_ede = (at_sum/N)**(1/(1-epsilon))
    at_ind = 1 - (at_ede/x_mean)
    return(at_ind, at_ede)

def get_kp(df, kapa, race):
    N = df[race].sum()
    x_mean = np.average(df['distance'], weights = df[race])/1000
    sum_ede = 0
    sum_ii = 0
    count = 0
    for x_n in df['distance']/1000:
        sum_ede += np.exp(-kapa*x_n)*df[race].iloc[count]
        sum_ii += np.exp(-kapa*(x_n-x_mean))*df[race].iloc[count]
        count += 1
    kp_ede = (-1/kapa)*np.log(sum_ede/N)
    kp_ind = -(1/kapa)*np.log(sum_ii/N)
    return(kp_ind, kp_ede)

def get_stats(df, race):
    pop_total = df[race].sum()
    df = df.sort_values(by='distance')
    hist_data = []
    count =0
    for i in df['distance']/1000:
        for pop in range(int(df[race].iloc[count])):
            hist_data.append(i)
        count += 1
    mean = np.mean(hist_data)
    max = np.max(hist_data)
    std = np.std(hist_data)
    cov = std/mean
    return(mean, max, std, cov)

def plot_gini(df):
    for race in races:
        pop_tot = df[race].sum()
        dist_tot = df.distance.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df[race].cumsum()/pop_tot*100
        df['dist_perc'] = df.distance.cumsum()/dist_tot*100
        plt.plot(df.pop_perc, df.dist_perc, label=race)
    plt.plot(np.arange(0,101,1), np.arange(0, 101, 1), '--', color='black', lw=0.5, label = 'Perfect Equality Line')
    plt.xlabel('% Residents')
    # xlabel
    plt.ylabel('% Distance')
    plt.xlim([0,None])
    plt.ylim([0,None])
    plt.title('Gini Curve'.format(loc='center'))
    plt.legend(loc='best')
    #Save figrue
    fig_out = '/homedirs/man112/access_inequality_index/data/results/{}_GINI_race_test.pdf'.format(context['city'])
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    plt.clf()

def plot_hist(df):

    fig, axes = plt.subplots(ncols=2,nrows=5, sharex=True, sharey=True, gridspec_kw={'hspace':0.5})
    for race, ax in zip(races, axes.flat):
        pop_tot = df[race].sum()
        df = df.sort_values(by='distance')
        hist_data = []
        count = 0
        for i in tqdm((df.distance)/1000):
            for pop in range(df[race].iloc[count]):
                hist_data.append(i)
        sns.distplot(hist_data, hist = True, kde = True, bins = int(100), label = race, ax=ax, color=random.choice(['red','blue','green','yellow','orange','purple', 'pink']), kde_kws={'color':'black'})
        ax.title.set_text(race)
    plt.xlim([0,20])
    plt.ylim([0,None])

    fig_out = '/homedirs/man112/access_inequality_index/data/results/{}_HIST_race_test.pdf'.format(context['city'])
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, format='pdf')#, bbox_inches='tight')
    plt.clf()

def plot_cdf(df):
    for race in races:
        pop_tot = df[race].sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df[race].cumsum()/pop_tot*100
        plt.plot(df.distance/1000, df.pop_perc, label = race)
    plt.plot(np.arange(0,100,100/10000), 10000*[100], '--')
    # ylabel
    plt.ylabel('% Residents')
    # xlabel
    plt.xlabel('Distance to the nearest supermakrt (km)'.format())
    plt.xlim([0,15])
    plt.ylim([0,None])
    #making the title todays date and the time_stamp
    plt.title('CDF: Distance to the nearest supermarket'.format(), loc='center')
    plt.legend(loc='best')

    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/data/results/{}_CDF_race_test.pdf'.format(context['city'])
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    plt.clf()

if __name__ == '__main__':
    main()
