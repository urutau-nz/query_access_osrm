'''
Plot the recovery of nearest distance to supermarkets
Case study Wilmington, NC with Hurricane Florence
'''
# user defined variables
state = 'nc'
import utils
from config import *
db, context = cfg_init(state)
import inequality_function
# import race_metrics
from datetime import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.style as style
style.use('fivethirtyeight')
import code
services = ['super_market']
# plot size
w = 5
h = w/1.618
ax = plt.axes()
plt.locator_params(nbins=4)
# import the nearest distance data for the supermarket and how that changes over time
db, context = cfg_init(state)
con = db['con']
cursor = db['con'].cursor()
sql = "SELECT DISTINCT time_stamp FROM nearest_florence ORDER BY time_stamp ASC"
times = pd.read_sql(sql, con)
# subtract the date so that it's in days since land fall
landfall_date = datetime(2018,9,14,7,0)
# init the results df
results = pd.DataFrame({'time_stamp':times.time_stamp.values})
results['days'] = (results.time_stamp - landfall_date)/ timedelta (days=1)
results = results.reindex(columns = ['time_stamp','days','mean','EDE_kp_a','equal_kp_a','EDE_kp_w','equal_kp_w','EDE_kp_b','equal_kp_b'])
# init kappa
kappa = None
# loop through dates
for service in services:
    for index, row in results.iterrows():
        # get the time stamp
        time_stamp = results.loc[index,'time_stamp']
        # read the distances
        sql = 'SELECT distance, id_orig FROM nearest_florence WHERE time_stamp = %s AND service = %s'
        distance = pd.read_sql(sql, con, params = (time_stamp, service,))
        distance['distance'] = distance.distance/1000
        # import number of people
        sql = 'SELECT "H7X001", "H7X002", geoid10 FROM demograph;'
        distribution = pd.read_sql(sql, con)
        # merge population into blocks
        distribution = distribution.merge(distance, left_on = 'geoid10', right_on = 'id_orig')
        # calculate the mean
        results.loc[index, 'mean'] = np.average(distribution.distance.values, weights = distribution.H7X001.values)
        # determine kappa
        if not kappa:
            kappa = inequality_function.calc_kappa(list(distribution.distance), -0.5, list(distribution.H7X001))
        results.loc[index,['EDE_kp_a']] = inequality_function.kolm_pollak_ede(list(distribution.distance), -0.5, kappa, list(distribution.H7X001))
        results.loc[index,['equal_kp_a']] = inequality_function.kolm_pollak_index(list(distribution.distance), -0.5, kappa, list(distribution.H7X001))
        #results.loc[index,['EDE_kp_w']] = inequality_function.kolm_pollak_ede(list(distribution.distance), -0.5, kappa, list(distribution.H7X002))
        #results.loc[index,['equal_kp_w']] = inequality_function.kolm_pollak_index(list(distribution.distance), -0.5, kappa, list(distribution.H7X002))
        #results.loc[index,['EDE_kp_b']] = inequality_function.kolm_pollak_ede(list(distribution.distance), -0.5, kappa, list(distribution.H7X001-distribution.H7X002))
        #results.loc[index,['equal_kp_b']] = inequality_function.kolm_pollak_index(list(distribution.distance), -0.5, kappa, list(distribution.H7X001-distribution.H7X002))
        # plot the results
        # if service == 'gas_station':
    #results['mean'] = results['mean'] - results.loc[0,'mean']

fig, ax1 = plt.subplots()
ax2 = ax1.twinx()
ax1.plot(results.days, results.EDE_kp_a)
ax2.plot(results.days, results.equal_kp_a, color='red')

ax1.set_xlabel('Days since landfall')
ax1.set_ylabel('EDE (km)')
ax2.set_ylabel('inequality index')
ax1.set_ylim([0,10])
ax1.set_yticks([0,2.5,5,7.5,10,12.5])
ax2.set_ylim([0,1.25])
ax2.set_yticks([0,0.25,0.5,0.75,1,1.25])
ax1.set_xlim([-5,10])

# flip the y axis
ax1.invert_yaxis()

# save
fig_out = '/homedirs/man112/access_inequality_index/fig/supermarket_restore.pdf'
if os.path.isfile(fig_out):
    os.remove(fig_out)
plt.savefig(fig_out,dpi=600,orientation='landscape',format='pdf',facecolor='w', edgecolor='w',transparent=True, bbox_inches="tight")
# plt.clf()
results.to_csv(r'/homedirs/man112/access_inequality_index/data/results/EDE_change.csv'.format())
#code.interact(local=locals())
db['con'].close()
