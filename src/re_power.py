'''
Plot the distribution of customer's power restoration times
Hurricane Matthew, 2016
Calculate the
'''
from mpl_toolkits import mplot3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.style as style
from pathlib import Path
style.use('fivethirtyeight')
from matplotlib import cm
import pandas as pd
import datetime
import seaborn as sns
import inequality_function
import os

utilities = ['DC_MD_Pepco','FL_DukeEnergy','FL_FloridaPower_Light','GA_GeorgiaPower','NC_SC_DukeEnergy','VA_DominionVirginiaPower']

def prepare_data():
    data_dir = "/homedirs/man112/access_inequality_index/data/power/2016-hurricane-matthew/"
    # loop txt files and append to df
    df = pd.DataFrame(columns=['datetime', 'area', 'cust_out','cust_total','util'])

    for utility in utilities:
        fname = data_dir + 'data_{}.txt'.format(utility)
        df_temp = pd.read_table(fname, delimiter = ",", engine='python', quoting=3)
        # remove the quotation
        df_temp['year'] = df_temp['"year'].map(lambda x: x.lstrip('"'))
        # get a datetime
        df_temp['datetime'] =  pd.to_datetime(df_temp[['year','month','day','hour','minute']])
        # drop columns except cust numbers
        df_temp = df_temp.loc[:, df_temp.columns.str.startswith('out') + df_temp.columns.str.startswith('total') + df_temp.columns.str.startswith('dateti')]
        df_out = df_temp.loc[:, df_temp.columns.str.startswith('out') + df_temp.columns.str.startswith('dateti')]
        df_total = df_temp.loc[:, df_temp.columns.str.startswith('total') + df_temp.columns.str.startswith('dateti')]
        # melt this data
        df_out = df_out.melt(id_vars='datetime',var_name='area',value_name='cust_out')
        df_total = df_total.melt(id_vars='datetime',var_name='area',value_name='cust_total')
        # remove 'out_' and 'total_' from start of area name
        df_out['area'] = df_out['area'].map(lambda x: x.lstrip('out_'))
        df_total['area'] = df_total['area'].map(lambda x: x.lstrip('total_'))
        # merge to create the new df to append
        df_new = df_out.merge(df_total, on=['datetime','area'])
        df_new['util'] = utility
        # appnd df
        df = df.append(df_new)
    # strip the whitespace from the area names
    df['area'] = df['area'].str.replace(" ","")
    # add percentage out
    df = df.loc[df.cust_total>0,]
    df['perc'] = df.cust_out/df.cust_total
    # get the distribution for the restoration
    df_restor_head = ['time_restore','customers','util','area']
    df_restor = list()
    # loop areas
    for area in df.area.unique():
        # get the subset for the area
        df_area = df.loc[df.area==area,]
        # loop through the time
        time = 0
        cust = 0
        for index, row in df_area.iterrows():
            # iterate time
            if cust == 0:
                time = 0
            # change in customers out
            cust_change = cust - row.cust_out
            if cust_change > 0:
                df_restor.append([time,cust_change,row.util,area])
            # update
            cust = row.cust_out
            # add more time
            time += 15 #min

    # restoration of electricity
    df_restor = pd.DataFrame(df_restor,columns=df_restor_head)
    df_restor.time_restore = df_restor.time_restore/60/24
    # save data
    df_restor.to_csv("/homedirs/man112/access_inequality_index/data/power/2016-hurricane-matthew/restore_times.csv")

    # impact of Hurricane
    df_impact = df.groupby(['area','util'])['perc'].max()
    df_impact = df_impact.reset_index()
    # save data
    df_impact.to_csv("/homedirs/man112/access_inequality_index/data/power/2016-hurricane-matthew/impact.csv")


# check histograms by utility weighted by custs
# for util in utilities:
#     df_restor_util = df_restor.loc[df_restor.util==util,]
#     df_restor_util['time_restore'].plot(kind='hist', weights=df_restor_util.customers,alpha=0.5)
    # a = np.histogram(a=df_restor_util.time_restore, weights=df_restor_util.customers)
    # _ = plt.hist(a)
def plot_ede():
    # import data
    df_restor = pd.read_csv("/homedirs/man112/access_inequality_index/data/power/2016-hurricane-matthew/restore_times.csv")
    df_impact = pd.read_csv("/homedirs/man112/access_inequality_index/data/power/2016-hurricane-matthew/impact.csv")
    ###
    # restoration of electricity
    ###
    #get ede for time to restore for each util
    #init results dataframe
    results = list()
    df_header=['util', 'mean', 'ede', 'ie','phase']
    # calculate the metrics
    kappa = inequality_function.calc_kappa(list(df_restor.time_restore), -0.5, list(df_restor.customers))
    print(kappa)
    for util in utilities:
        # subset by utility
        df_u = df_restor.set_index('util').copy()
        df_u = df_u.loc[util]
        # calculate metrics
        recov_mean = np.average(list(df_u.time_restore), weights = list(df_u.customers))
        recov_ede = inequality_function.kolm_pollak_ede(list(df_u.time_restore), -0.5, kappa, list(df_u.customers))
        recov_ie = inequality_function.kolm_pollak_index(list(df_u.time_restore), -0.5, kappa, list(df_u.customers))
        # save to results`
        new_result = [util, recov_mean, recov_ede, recov_ie, 'restore']
        results.append(new_result)
    ###
    # impact of Hurricane
    ###
    kappa = inequality_function.calc_kappa(list(df_impact.perc), -0.5)
    print(kappa)
    for util in utilities:
        # subset by utility
        df_i = df_impact.set_index('util').copy()
        df_i = df_i.loc[util]
        # calculate metrics
        impact_mean = df_i.perc.mean()
        impact_ede = inequality_function.kolm_pollak_ede(list(df_i.perc), kappa=kappa)
        impact_ie = inequality_function.kolm_pollak_index(list(df_i.perc), kappa=kappa)
        # save to results`
        new_result = [util, impact_mean, impact_ede, impact_ie, 'impact']
        results.append(new_result)
    # create DataFrame
    results = pd.DataFrame(results, columns=df_header)
    # save results
    results.to_csv("/homedirs/man112/access_inequality_index/fig/power_restore.csv")
    print(results)
    ###
    # plot
    ###
    # scale the results for plot
    results.loc[results.phase == 'impact','ede'] *= -10# results.ede[results.phase == 'impact'] * 10
    results.loc[results.phase == 'restore','ede'] *= 1 #    results.restore = results.restore * -1
    # pivot
    results = results.pivot(index='util', columns='phase', values='ede')
    results = results.sort_values(by=['impact'], ascending = True)
    # plot
    ax = results.plot(y='impact',kind='bar',color='red')
    results.plot(y='restore',kind='bar', ax=ax)
    plt.ylim([-4.5,4.5])
    # save plot
    fig_out = '/homedirs/man112/access_inequality_index/fig/power_restore.pdf'
    if os.path.isfile(fig_out):
        os.remove(fig_out)
    plt.savefig(fig_out,dpi=600,orientation='landscape',format='pdf',facecolor='w', edgecolor='w',transparent=True, bbox_inches="tight")
