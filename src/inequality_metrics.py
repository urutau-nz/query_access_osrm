

# User defined variables
# Will compare the
beta = -0.5
epsilon = 0.5
states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'il', 'wa', 'tx']
file_name = 'test_results_cleaned'

import utils
from config import *


def main():
    city, data = get_data()
    kapa = calc_kapa(data)
    results = pd.DataFrame(np.nan, index=np.arange(10), columns=['State','City', 'Kapa', 'Beta', 'Epsilon', 'Kolm-Pollak EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm-Pollak Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation'])
    results.State = states
    results = results.set_index('State')
    for state in states:
        df = data['{}_data'.format(state)]
        results.City = city
        results.loc[state, 'Kapa'], results.loc[state, 'Beta'], results.loc[state, 'Epsilon'] = kapa, beta, epsilon
        results.loc[state, 'Kolm-Pollak Index'], results.loc[state, 'Kolm-Pollak EDE'] = get_kp(df, kapa)
        results.loc[state, 'Atkinson Index'], results.loc[state, 'Atkinson EDE'] = get_at(df)
        results.loc[state, 'Atkinson Adjusted Index'], results.loc[state, 'Atkinson Adjusted EDE'] = get_at_adj(df)
        results.loc[state, 'Gini Index'] = get_gini(df)
        results.loc[state, 'Distribution Mean'], results.loc[state, 'Distribution Max'], results.loc[state, 'Distribution Standard Deviation'], results.loc[state, 'Distribution Coefficient of Variation'] = get_stats(df)

    plot_gini(data)
    plot_hist(data)
    plot_cdf(data)

    results.to_csv(r'/homedirs/man112/access_inequality_index/data/results/{}.csv'.format(file_name))

def get_data():
    data = {}
    city = []
    for state in states:
        db, context = cfg_init(state)
        cursor = db['con'].cursor()
        sql = 'SELECT * FROM distxdem'
        data["{}_data".format(state)] = pd.read_sql(sql, db["con"])
        db['con'].close()
        city.append(context['city'])
        df = data['{}_data'.format(state)]
        df = df.loc[df['distance'] !=0]
        df = df.loc[df['H7X001'] !=0]
        data['{}_data'.format(state)] = df
    return(city, data)

def calc_kapa(data):
    kapa_data = []
    for state in states:
        df = data['{}_data'.format(state)]
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
    return(kapa)

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

    fig, axes = plt.subplots(ncols=2,nrows=5, sharex=True, sharey=True, gridspec_kw={'hspace':0.5})
    print('Collecting Histogram Data')
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
        ax.title.set_text(state)
    plt.xlim([0,20])
    plt.ylim([0,None])

    fig_out = '/homedirs/man112/access_inequality_index/data/results/HIST_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, format='pdf')#, bbox_inches='tight')
    plt.clf()

def plot_cdf(data):
    for state in states:
        df = data['{}_data'.format(state)]
        pop_tot = df.H7X001.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df.H7X001.cumsum()/pop_tot*100
        plt.plot(df.distance/1000, df.pop_perc, label = state)
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
    fig_out = '/homedirs/man112/access_inequality_index/data/results/CDF_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    plt.clf()

if __name__ == '__main__':
    main()
