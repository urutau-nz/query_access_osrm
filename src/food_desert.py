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
cities = {'md':'baltimore','fl':'miami','co':'denver','mi':'detroit','la':'new orleans','ga':'atlanta','or':'portland','il':'chicago','wa':'seattle','tx':'houston'}
file_name = 'food_des_{}'.format(beta)
weight_code = 'H7X001'

# Imports
import utils
from config import *
import inequality_function
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.style as style
style.use('fivethirtyeight')
w = 5
h = w/1.618

def main():
    '''Creates dataframe and adds data for each city before plotting and exporting CSV'''
    city, data = get_data() # data is a dictionary of dataframes for each state
    kappa_data = get_kappa_data(data)
    kappa = inequality_function.calc_kappa(kappa_data, beta) # kappa is based on the distances from ALL states and the beta provided
    results = pd.DataFrame(np.nan, index=np.arange(10), columns=['State','City', 'Kappa', 'Beta', 'Epsilon', 'Kolm-Pollak EDE', 'Atkinson EDE', 'Atkinson Adjusted EDE', 'Kolm-Pollak Index', 'Atkinson Index', 'Atkinson Adjusted Index', 'Gini Index', 'Distribution Mean', 'Distribution Max', 'Distribution Standard Deviation', 'Distribution Coefficient of Variation'])
    results.State = states
    results = results.set_index('State')
    for state in states:
        # Gets the df for specific state
        df = data['{}_data'.format(state)].copy()
        # drop data that has 0 weight
        df = df.iloc[np.array(df[weight_code]) > 0].copy()
        a = list(df.distance)
        at = list(1/df.distance)
        weight = list(df[weight_code])
        # adds the city name
        results.City = city
        # adds aversion params
        results.loc[state, 'Kappa'], results.loc[state, 'Beta'], results.loc[state, 'Epsilon'] = kappa, beta, epsilon
        # adds all Kolm-Pollak metrics
        results.loc[state, 'Kolm-Pollak Index'], results.loc[state, 'Kolm-Pollak EDE'] = inequality_function.kolm_pollak_index(a, beta, kappa, weight), inequality_function.kolm_pollak_ede(a, beta, kappa, weight)
        # adds all normal (with inverted x) atkinson metrics
        results.loc[state, 'Atkinson Index'], results.loc[state, 'Atkinson EDE'] = inequality_function.atkinson_index(at, epsilon, weight), inequality_function.atkinson_ede(at, epsilon, weight)
        # adds all adjusted atkinson metrics
        results.loc[state, 'Atkinson Adjusted Index'], results.loc[state, 'Atkinson Adjusted EDE'] = inequality_function.atkinson_adjusted_index(a, beta, weight), inequality_function.atkinson_adjusted_ede(a, beta, weight)
        # adds gini
        results.loc[state, 'Gini Index'] = inequality_function.gini_index(a, beta, weight)
        # adds all summary stats from the distribution
        results.loc[state, 'Distribution Mean'], results.loc[state, 'Distribution Max'], results.loc[state, 'Distribution Standard Deviation'], results.loc[state, 'Distribution Coefficient of Variation'] = get_stats(df)

    #plot_gini(data)
    #plot_hist(data)
    #plot_cdf(data)
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/food_des/{}_{}.csv'.format(file_name,weight_code))

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

def get_kappa_data(data):
    '''takes dictionary of dataframes, and global beta, minimised the sum of squares for all data to return kappa'''
    kappa_data = [] # init empty list for each distance
    for state in states:
        df = data['{}_data'.format(state)]
        count = 0
        for i in df['distance']: #takes each distance
            for pop in range(int(df['H7X001'].iloc[count])): #adds the distance to the list as many times as there are people in the block
                kappa_data.append(i)
            count += 1
    return(kappa_data)

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

def get_kolm(df, kappa):
    '''takes a dataframe with pop and dist, and a kappa value. returns Kolm-Pollak EDE and Index'''
    N = df['H7X001'].sum() # total pop
    x_mean = np.average(df['distance'], weights = df['H7X001']) # mean of dist weighted by pop
    sum_ede = 0 # init sum
    sum_ii = 0 # init sum
    count = 0
    for x_n in df['distance']:
        sum_ede += np.exp(-kappa*x_n)*df['H7X001'].iloc[count]
        sum_ii += np.exp(-kappa*(x_n-x_mean))*df['H7X001'].iloc[count]
        count += 1
    kp_ede = (-1/kappa)*np.log(sum_ede/N) #EDE
    kp_ind = -(1/kappa)*np.log(sum_ii/N) # Index
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

def plot_cdf(data=None):
    '''takes dictionary of dataframes with pop and dist. returns cdf'''
    if data is None:
        # file_name = 'food_des_{}'.format(beta)
        city, data = get_data()
    percentiles = pd.DataFrame()
    for state in states:
        df = data['{}_data'.format(state)] #gets correct dataframe
        pop_tot = df.H7X001.sum()
        df = df.sort_values(by='distance')
        df['pop_perc'] = df.H7X001.cumsum()/pop_tot*100 #percentage of pop
        df['state'] = state
        plt.plot(df.distance, df.pop_perc, label = state) #plot the cdf
        percentiles = percentiles.append(df[['state','distance','pop_perc']], ignore_index=True)
    # plt.plot(np.arange(0,100,100/10000), 10000*[100], '--') #plot y=100% line
    # labels
    plt.ylabel('% Residents')
    plt.xlabel('Distance to the nearest supermarket (km)'.format())
    plt.title('CDF: Distance to the nearest supermarket'.format(), loc='center')
    plt.legend(loc='best')
    # limits
    plt.xlim([0,15])
    plt.ylim([0,None])
    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/data/results/food_des/CDF.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=False)#, bbox_inches='tight')
    # plt.clf()
    # save the percentiles as a dataframe as well
    percentiles['keep'] = False
    for p in [10,50,75,90,95,100]:
        percentiles['dif'] = (percentiles.pop_perc-p).abs()
        percentiles.loc[percentiles.groupby('state')['dif'].idxmin(),'keep'] = True
    print(percentiles)
    percentiles = percentiles.loc[percentiles.keep,]
    percentiles['pop_perc'] = percentiles['pop_perc'].round(0).apply(str)
    percentiles['distance'] = percentiles['distance'].round(2)
    percentiles = percentiles.drop_duplicates(["state", "pop_perc"])
    percentiles = percentiles.pivot(index='state', columns='pop_perc', values='distance')
    print(percentiles)
    percentiles.to_csv('/homedirs/man112/access_inequality_index/data/results/food_des/distance_percentiles.csv')


def plot_cdf_dems(data = None):
    '''plots a cdf from a data frame'''
    if not data:
        # file_name = 'food_des_{}'.format(beta)
        city, data = get_data()

    for state in ['tx','il']:
        for race in ['H7X001','H7X002','H7X003','H7Y003']:
            df = data['{}_data'.format(state)].copy() #gets correct dataframe
            pop_tot = df[race].sum()
            df = df.sort_values(by='distance')
            df['pop_perc'] = df[race].cumsum()/pop_tot*100 #percentage of pop
            plt.plot(df.distance, df.pop_perc, label = state+'_'+race) #plot the cdf
    # plt.plot(np.arange(0,100,100/10000), 10000*[100], '--') #plot y=100% line
    # labels
    plt.ylabel('% Residents')
    plt.xlabel('Distance to the nearest supermakrt (km)'.format())
    # plt.title('CDF: Distance to the nearest supermarket'.format(), loc='center')
    plt.legend(loc='best')
    # limits
    plt.xlim([0,10])
    plt.ylim([0,None])
    # horizontal line at 0
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    # vertical line on left
    # plt.set_xlim(left = 0, right = 10)
    # background
    # plt.set_facecolor('w')
    # savefig
    fig_out = '/homedirs/man112/access_inequality_index/fig/CDF_fooddesert_bestworst.pdf'.format()
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    # plt.clf()

def plot_edes(data = None):
    '''plots the ede and inequality indices'''
    if not data:
        file_name = 'food_des_{}'.format(beta)
        data = pd.read_csv('/homedirs/man112/access_inequality_index/data/results/food_des/{}_{}.csv'.format(file_name, weight_code))

    # sort the data by the KP EDE
    data = data.sort_values(by='Kolm-Pollak EDE')
    # print(data)
    # plot on a line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=4)
    data.plot(x="City", y=["Kolm-Pollak EDE", "Atkinson EDE", "Atkinson Adjusted EDE", "Distribution Mean"],ax=ax)
    plt.ylim([0, 4])
    plt.xticks(range(10),data.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/ede_compare.pdf'.format()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()
    plt.clf()

    # plot the indices on another line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=3)
    data.plot(x="City", y=["Kolm-Pollak Index", "Atkinson Index", "Atkinson Adjusted Index", "Distribution Coefficient of Variation", "Gini Index"],ax=ax)
    plt.ylim([0, 1])
    plt.xticks(range(10),data.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/index_compare.pdf'.format()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()

def plot_edes_dem():
    '''plots the ede and inequality indices'''

    # get the data
    city, data = get_data() # data is a dictionary of dataframes for each state
    kappa_data = get_kappa_data(data)
    kappa = inequality_function.calc_kappa(kappa_data, beta) # kappa is based on the distances from ALL states and the beta provided
    results = pd.DataFrame(np.nan, index=np.arange(10), columns=['State','City', 'KP_EDE_H7X001', 'KP_IE_H7X001', 'KP_EDE_H7X002', 'KP_IE_H7X002', 'KP_EDE_H7X003', 'KP_IE_H7X003','KP_EDE_H7X004', 'KP_IE_H7X004','KP_EDE_H7X005', 'KP_IE_H7X005','KP_EDE_H7Y003', 'KP_IE_H7Y003'])
    # adds the city name
    results.State = states
    results = results.set_index('State')
    results.City = city
    for state in states:
        # Gets the df for specific state
        df = data['{}_data'.format(state)].copy()
        # loop demographic
        for race in ['H7X001','H7X002','H7X003','H7X004','H7X005','H7Y003']:
            # drop data that has 0 weight
            dr = df.iloc[np.array(df[race]) > 0].copy()
            a = list(dr.distance)
            at = list(1/dr.distance)
            weight = list(dr[race])
            # adds all Kolm-Pollak metrics
            results.loc[state, 'KP_EDE_{}'.format(race)], results.loc[state, 'KP_IE_{}'.format(race)] = inequality_function.kolm_pollak_ede(a, kappa = kappa, weight = weight), inequality_function.kolm_pollak_index(a, kappa = kappa, weight = weight)

    print(results)
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/food_des/ede_dems_{}.csv'.format(beta))
    # sort the data by the KP EDE
    results = results.sort_values(by='KP_EDE_H7X001')
    # plot on a line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=4)
    results.plot(x="City", y=["KP_EDE_H7X001", "KP_EDE_H7X002", "KP_EDE_H7X003","KP_EDE_H7Y003"],ax=ax)
    plt.ylim([0, None])
    plt.xticks(range(10),results.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/ede_race_compare.pdf'.format()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    plt.show()
    plt.clf()

    # plot the indices on another line graph
    ax = plt.axes()
    plt.locator_params(axis='y', nbins=3)
    results.plot(x="City", y=["KP_IE_H7X001", "KP_IE_H7X002", "KP_IE_H7X003", "KP_IE_H7Y003"],ax=ax)
    plt.ylim([0, 1])
    plt.xticks(range(10),results.City)
    plt.xticks(rotation=90)
    plt.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
    fig_out = '/homedirs/man112/access_inequality_index/fig/index_race_compare.pdf'.format()
    # plt.show()
    plt.savefig(fig_out, dpi=500, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')


def sensitivity_aversion():
    ''' plot how the EDE and IE changes with beta '''
    # get the data
    city, data = get_data() # data is a dictionary of dataframes for each state
    kappa_data = get_kappa_data(data)
    # initiate list
    results = list()
    # loop through beta values
    for beta in np.concatenate(([-0.01,-0.25,-0.5,-0.75, -1.5, -2],np.logspace(0,1)*-1),axis=None):#[0,-0.25,-0.5,-0.75,-1,-2,-5,-10,-100]:
        # calculate kappa from beta
        kappa = inequality_function.calc_kappa(kappa_data, beta) # kappa is based on the distances from ALL states and the beta provided
        # calculate the ede for each city
        for state in states:#['il','tx','fl']:
            # get the data subset
            df = data['{}_data'.format(state)].copy()
            a = list(df.distance)
            weight = list(df['H7X001'])
            # calculate the values
            ede, ie = inequality_function.kolm_pollak_ede(a, kappa = kappa, weight = weight), inequality_function.kolm_pollak_index(a, kappa = kappa, weight = weight)
            # add to list
            new_result = [cities[state], beta, ede, ie]
            results.append(new_result)
    # make list of lists a dataframe
    results = pd.DataFrame(results, columns = ['city','beta','ede','ie'])
    results_ede = results.pivot(index='beta', columns='city', values='ede')
    results_ie = results.pivot(index='beta', columns='city', values='ie')

    print(results)

    # plot the results
    results_ede.plot()
    plt.gca().invert_xaxis()
    fig_out = '/homedirs/man112/access_inequality_index/fig/sensitivity_aversion.pdf'
    plt.savefig(fig_out, dpi=800, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')
    # results_ie.plot()
    # plt.gca().invert_xaxis()

    # plot a selection of betas
    results_beta = results.copy()
    results_beta['beta'] = results_beta['beta'].round(2).apply(str)
    results_beta = results_beta.pivot(index='city', columns='beta', values='ede')
    results_beta = results_beta.sort_values(by='-0.5')
    print(results_beta)
    results_beta.plot(y=['-0.25','-0.5','-0.75','-1.0','-1.5','-2.0'])
    plt.xticks(range(10),results_beta.index)
    plt.xticks(rotation=90)
    fig_out = '/homedirs/man112/access_inequality_index/fig/sensitivity_aversion_cities.pdf'
    plt.savefig(fig_out, dpi=800, format='pdf', transparent=True, bbox_inches='tight',facecolor='w')


def city_dems():
    ''' get a table with information about the cities '''
    city, data = get_data()
    # initiate list
    results = list()
    # loop the states/cities
    for state in states:
        df = data['{}_data'.format(state)].copy()
        pop_total = df['H7X001'].sum()
        perc_white = df['H7X002'].sum()/pop_total*100
        perc_black = df['H7X003'].sum()/pop_total*100
        perc_nindian = df['H7X004'].sum()/pop_total*100
        perc_asian = df['H7X005'].sum()/pop_total*100
        perc_latin = df['H7Y003'].sum()/pop_total*100
        new_result = [cities[state], pop_total, perc_white, perc_black, perc_nindian, perc_asian, perc_latin]
        # add to results
        results.append(new_result)
    # make list to DataFrame
    results = pd.DataFrame(results, columns=['City','Population','% White','% Black','% Am. Indian','% Asian','% Latino'])
    results = results.round(1)
    results = results.set_index('City')
    results.to_csv('/homedirs/man112/access_inequality_index/data/results/food_des/city_dems.csv')
    print(results)


if __name__ == '__main__':
    main()
