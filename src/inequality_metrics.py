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
beta = -0.5
epsilon = 0.5
states = ['md','fl', 'co', 'mi', 'la', 'ga', 'or', 'il', 'wa', 'tx']
file_name = 'full_city_compare_{}'.format(beta)

# Imports
import utils
from config import *

def main():
    '''Creates dataframe and adds data for each city before plotting and exporting CSV'''
    city, data = get_data() # data is a dictionary of dataframes for each state
    kapa = calc_kapa(data) # kapa is based on the distances from ALL states and the beta provided
    results = pd.DataFrame(np.nan, index=np.arange(10), columns=['State','City', 'Kapa', 'Beta', 'Epsilon', 'Kolm-Pollak EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm-Pollak Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation'])
    results.State = states
    results = results.set_index('State')
    for state in states:
        # Gets the df for specific state
        df = data['{}_data'.format(state)]
        # adds the city name
        results.City = city
        # adds aversion params
        results.loc[state, 'Kapa'], results.loc[state, 'Beta'], results.loc[state, 'Epsilon'] = kapa, beta, epsilon
        # adds all Kolm-Pollak metrics
        results.loc[state, 'Kolm-Pollak Index'], results.loc[state, 'Kolm-Pollak EDE'] = get_kolm(df, kapa)
        # adds all normal (with inverted x) atkinson metrics
        results.loc[state, 'Atkinson Index'], results.loc[state, 'Atkinson EDE'] = get_at(df)
        # adds all adjusted atkinson metrics
        results.loc[state, 'Atkinson Adjusted Index'], results.loc[state, 'Atkinson Adjusted EDE'] = get_at_adj(df)
        # adds gini
        results.loc[state, 'Gini Index'] = get_gini(df)
        # adds all summary stats from the distribution
        results.loc[state, 'Distribution Mean'], results.loc[state, 'Distribution Max'], results.loc[state, 'Distribution Standard Deviation'], results.loc[state, 'Distribution Coefficient of Variation'] = get_stats(df)

    plot_gini(data)
    plot_hist(data)
    plot_cdf(data)
    results.to_csv(r'/homedirs/man112/access_inequality_index/data/results/{}.csv'.format(file_name))

def get_data():
    '''fills a dictionary of dataframes for each state'''
    data = {} # init empty dictionary
    city = [] #init empty list of cities to return for the results
    for state in states:
        db, context = cfg_init(state)
        cursor = db['con'].cursor()
        sql = 'SELECT * FROM distxdem'
        data["{}_data".format(state)] = pd.read_sql(sql, db["con"])
        db['con'].close()
        city.append(context['city'])
        df = data['{}_data'.format(state)]
        df = df.loc[df['distance'] !=0] # removes all rows with 0 distance
        df = df.loc[df['H7X001'] !=0] # removes all rows with 0 population
        df.distance = df.distance/1000 # converts from meters to Kms
        data['{}_data'.format(state)] = df # replaces the dataframe in the dictionary
    return(city, data)

def calc_kapa(data):
    '''takes dictionary of dataframes, and global beta, minimised the sum of squares for all data to return kapa'''
    kapa_data = [] # init empty list for each distance
    for state in states:
        df = data['{}_data'.format(state)]
        count = 0
        for i in df['distance']: #takes each distance
            for pop in range(int(df['H7X001'].iloc[count])): #adds the distance to the list as many times as there are people in the block
                kapa_data.append(i)
            count += 1

    # minimises the sum of squares to return kapa
    x_sum = 0
    x_sq_sum = 0
    for i in kapa_data:
        x_sum += i
        x_sq_sum += i**2
    kapa = beta*(x_sum/x_sq_sum)
    return(kapa)

def get_gini(df):
    '''Calculates area between x=y line and the created lorenz curve and returns the gini index'''
    dist_tot = df['distance'].sum() # gives the total distance
    pop_tot = df['H7X001'].sum() #gives total population
    df = df.sort_values(by='distance') #sorts by distance
    df['pop_perc'] = df['H7X001'].cumsum()/pop_tot*100 #assigns percentage of population
    df['dist_perc'] = df['distance'].cumsum()/dist_tot*100 # assigns percentage of distance
    area_tot = simps(np.arange(0,101,1), dx=1) #Calculates the area under the x=y curve
    area_real = simps(df['dist_perc'], df['pop_perc']) # calculates the area under the lorenz curve
    area_diff = area_tot - area_real # gives area between lorenz and x=y
    gini = area_diff/area_tot
    gini = round(gini, 3)
    return(gini)

def get_at_adj(df):
    '''takes a dataframe with pop and dist, uses beta to calc EDE and index'''
    at_sum = 0 # init sum
    count = 0
    N = df['H7X001'].sum() #total population
    x_mean = np.average(df['distance'], weights = df['H7X001']) #gives weighted mean for the distance
    for i in df['distance']:
        at_sum += (i**(1-beta))*df['H7X001'].iloc[count] #sum function from atkinson eqn
        count += 1
    at_ede = (at_sum/N)**(1/(1-beta)) # EDE
    at_ind = (at_ede/x_mean)-1 # Index
    return(at_ind, at_ede)

def get_at(df):
    '''takes a dataframe with pop and dist, returns normal atkinson metrics for a "bad" distribution by inverting the distance value'''
    at_sum = 0 # init sum
    N = df['H7X001'].sum() # total pop
    x_mean = np.average(df['distance'], weights = df['H7X001']) # mean of dist weighted by pop
    count = 0
    for i in df['distance']:
        i = 1/i #inverts distance
        at_sum += (i**(1-epsilon))*df['H7X001'].iloc[count] #atkinson eqn sum
        count += 1
    at_ede = (at_sum/N)**(1/(1-epsilon)) #EDE
    at_ind = 1 - (at_ede/x_mean) # Index
    return(at_ind, at_ede)

def get_kolm(df, kapa):
    '''takes a dataframe with pop and dist, and a kapa value. returns Kolm-Pollak EDE and Index'''
    N = df['H7X001'].sum() # total pop
    x_mean = np.average(df['distance'], weights = df['H7X001']) # mean of dist weighted by pop
    sum_ede = 0 # init sum
    sum_ii = 0 # init sum
    count = 0
    for x_n in df['distance']:
        sum_ede += np.exp(-kapa*x_n)*df['H7X001'].iloc[count]
        sum_ii += np.exp(-kapa*(x_n-x_mean))*df['H7X001'].iloc[count]
        count += 1
    kp_ede = (-1/kapa)*np.log(sum_ede/N) #EDE
    kp_ind = -(1/kapa)*np.log(sum_ii/N) # Index
    return(kp_ind, kp_ede)

def get_stats(df):
    '''provides Mean, Max, STD, COV for distribution of dist and pop'''
    pop_total = df['H7X001'].sum()
    df = df.sort_values(by='distance')
    hist_data = [] #init list for distribution data
    count = 0
    for i in df['distance']:
        for pop in range(int(df['H7X001'].iloc[count])):
            hist_data.append(i) #for each person in block, appends the distance
        count += 1
    mean = np.mean(hist_data)
    max = np.max(hist_data)
    std = np.std(hist_data)
    cov = std/mean
    return(mean, max, std, cov)

def plot_gini(data):
    '''Takes dictionary of dataframes and plots gini on one plot'''
    for state in states:
        df = data['{}_data'.format(state)] #gets the right dataframe
        pop_tot = df.H7X001.sum()
        dist_tot = df.distance.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df.H7X001.cumsum()/pop_tot*100
        df['dist_perc'] = df.distance.cumsum()/dist_tot*100
        plt.plot(df.pop_perc, df.dist_perc, label=state) # plots gini curve for state
    plt.plot(np.arange(0,101,1), np.arange(0, 101, 1), '--', color='black', lw=0.5, label = 'Perfect Equality Line') # plots perfect equality line, x=y
    # labels
    plt.xlabel('% Residents')
    plt.ylabel('% Distance')
    plt.title('Gini Curve'.format(loc='center'))
    plt.legend(loc='best')
    # limits
    plt.xlim([0,None])
    plt.ylim([0,None])
    #Save figrue
    fig_out = '/homedirs/man112/access_inequality_index/data/results/GINI_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    plt.clf()

def plot_hist(data):
    '''takes dictionary of dataframes and plots a histogram on subplots'''
    fig, axes = plt.subplots(ncols=2,nrows=5, sharex=True, sharey=True, gridspec_kw={'hspace':0.5}) #set up subplots
    print('Collecting Histogram Data')
    for state, ax in zip(states, axes.flat):
        df = data['{}_data'.format(state)] #get the right df
        pop_tot = df.H7X001.sum()
        df = df.sort_values(by='distance')
        hist_data = [] #init list for distribution data
        count = 0
        for i in tqdm((df.distance)):
            for pop in range(df.H7X001.iloc[count]):
                hist_data.append(i) #for each person in block, appends distance
        sns.distplot(hist_data, hist = True, kde = True, bins = int(100), label = state, ax=ax, color=random.choice(['red','blue','green','yellow','orange','purple', 'pink']), kde_kws={'color':'black'}) #plots hist
        ax.title.set_text(state)
    plt.xlim([0,20])
    plt.ylim([0,None])
    # save fig
    fig_out = '/homedirs/man112/access_inequality_index/data/results/HIST_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, format='pdf')#, bbox_inches='tight')
    plt.clf()

def plot_cdf(data):
    '''takes dictionary of dataframes with pop and dist. returns cdf'''
    for state in states:
        df = data['{}_data'.format(state)] #gets correct dataframe
        pop_tot = df.H7X001.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df.H7X001.cumsum()/pop_tot*100 #percentage of pop
        plt.plot(df.distance, df.pop_perc, label = state) #plot the cdf
    plt.plot(np.arange(0,100,100/10000), 10000*[100], '--') #plot y=100% line
    # labels
    plt.ylabel('% Residents')
    plt.xlabel('Distance to the nearest supermakrt (km)'.format())
    plt.title('CDF: Distance to the nearest supermarket'.format(), loc='center')
    plt.legend(loc='best')
    # limits
    plt.xlim([0,15])
    plt.ylim([0,None])
    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/data/results/CDF_test.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    plt.clf()

if __name__ == '__main__':
    main()
