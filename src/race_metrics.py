'''
For given beta and states, will take data from SQL with population and distance and provide:
    Kolm-Pollak Index & EDE
    Atkinson Index & EDE
    Adjusted Atkinson Index and EDE
    Gini Index
    Plot of Gini, CDF and Distribution
    Distribution summary statistics
'''

# User defined variables
kapa = -0.170477678 #This should be equal to kapa used for city comparisons
beta = -0.5
epsilon = 0.5
races = ['H7X001', 'H7X002', 'H7X003', 'H7X004', 'H7X005', 'H7Y003']
race_labels = ['all', 'white', 'black', 'american_indian', 'asian', 'hispanic'] #Black and african american, indiand and native alaskan, hispanic and latino
state = input('State: ')

#imports
import utils
from config import *
db, context = cfg_init(state)
cursor = db['con'].cursor()

file_name = '{}_race_results'.format(context['city'])

def main():
    df, city = get_df()
    results = pd.DataFrame(np.nan, index=np.arange(6), columns=['State', 'City', 'Race', 'Race_Label', 'Kapa', 'Beta', 'Epsilon', 'Kolm-Pollak EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm-Pollak Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation'])
    # adds race
    results.Race_Label = race_labels
    results.Race = races
    #sets index to race
    results = results.set_index('Race')
    for race in races:
        # adds the city name
        results.City = city
        # adds aversion params
        results.loc[race, 'Kapa'], results.loc[race, 'Beta'], results.loc[race, 'Epsilon'] = kapa, beta, epsilon
        # adds all Kolm-Pollak metrics
        results.loc[race, 'Kolm-Pollak Index'], results.loc[race, 'Kolm-Pollak EDE'] = get_kolm(df, kapa, race)
        # adds all normal (with inverted x) atkinson metrics
        results.loc[race, 'Atkinson Index'], results.loc[race, 'Atkinson EDE'] = get_at(df, race)
        # adds all adjusted atkinson metrics
        results.loc[race, 'Atkinson Adjusted Index'], results.loc[race, 'Atkinson Adjusted EDE'] = get_at_adj(df, race)
        # adds gini
        results.loc[race, 'Gini Index'] = get_gini(df, race)
        # adds all summary stats from the distribution
        results.loc[race, 'Distribution Mean'], results.loc[race, 'Distribution Max'], results.loc[race, 'Distribution Standard Deviation'], results.loc[race, 'Distribution Coefficient of Variation'] = get_stats(df, race)

    plot_gini(df)
    plot_hist(df)
    plot_cdf(df)
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
    df = df.loc[df['H7X001'] !=0]
    df = df.dropna()
    return(df, city)

def get_gini(df, race):
    df = df.loc[df[race]!=0]
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
    df = df.loc[df[race]!=0]
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
    df = df.loc[df[race]!=0]
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

def get_kolm(df, kapa, race):
    df = df.loc[df[race]!=0]
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
    df = df.loc[df[race]!=0]
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
        df = df.loc[df[race]!=0]
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

    fig, axes = plt.subplots(ncols=2,nrows=3, sharex=True, sharey=True, gridspec_kw={'hspace':0.5})
    for race, ax in zip(races, axes.flat):
        df = df.loc[df[race]!=0]
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
        df = df.loc[df[race]!=0]
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
