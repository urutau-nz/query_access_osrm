'''
Plot the recovery of nearest distance to supermarkets
Case study Wilmington, NC with Hurricane Florence
'''
# user defined variables
state = 'nc'

import utils
from config import *
db, context = cfg_init(state)
import inequality_metrics
# import race_metrics
from datetime import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.style as style
style.use('fivethirtyeight')
import code

service = 'super_market'
# import the nearest distance data for the supermarket and how that changes over time
db, context = cfg_init(state)
con = db['con']
cursor = db['con'].cursor()
sql = "SELECT DISTINCT time_stamp FROM nearest_florence WHERE service='super_market' ORDER BY time_stamp ASC"
times = pd.read_sql(sql, db["con"])

# subtract the date so that it's in days since land fall
landfall_date = datetime(2018,9,14,7,0)

# init the results df
results = pd.DataFrame({'time_stamp':times.time_stamp.values})
results['days'] = (results.time_stamp - landfall_date)/ timedelta (days=1)
results = results.reindex(columns = ['time_stamp','days','mean','EDE_kp_a','equal_kp_a','EDE_kp_w','equal_kp_w','EDE_kp_b','equal_kp_b'])

# init kappa
kappa = None

# loop through dates
for index, row in results.iterrows():
    # get the time stamp
    time_stamp = results.loc[index,'time_stamp']
    # read the distances
    sql = 'SELECT distance, id_orig FROM nearest_florence WHERE time_stamp = %s AND service = %s'
    distance = pd.read_sql(sql, con, params = (time_stamp, service,))
    # import number of people
    sql = 'SELECT "H7X001", "H7X002", geoid10 FROM demograph;'
    distribution = pd.read_sql(sql, con)
    # merge population into blocks
    distribution = distribution.merge(distance, left_on = 'geoid10', right_on = 'id_orig')
    # calculate the mean
    results.loc[index, 'mean'] = np.average(distribution.distance.values, weights = distribution.H7X001.values)
    # determine kappa
    # if not kappa:
        # kappa = calc_kapa()
    # results.loc[index,['EDE_kp_a','equal_kp_a']] = inequality_metrics.get_kp()
    # results.loc[index,['EDE_kp_w','equal_kp_w']] = race_metrics.get_kp()
    # results.loc[index,['EDE_kp_b','equal_kp_b']] = race_metrics.get_kp()

# plot the results
w = 5
h = w/1.618
f1 = results.plot(x='days', y='mean', figsize = (w,h), legend = False)
# horizontal line at 0
# f1.axhline(y = 0, color = 'black', linewidth = 1.3, alpha = .7)
# vertical line on left
f1.set_xlim(left = -5, right = 15)
f1.set_ylim([0,6000])
# axis labels
f1.tick_params(axis = 'both', which = 'major', labelsize = 10)
# flip y axis
plt.gca().invert_yaxis()
# save
plt.show()




db['con'].close()
