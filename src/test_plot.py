import plotly.graph_objects as go
import numpy as np
import pandas as pd
import plotly
from statsmodels.distributions.empirical_distribution import ECDF
from config import *

# Load dataset
data1 = np.random.binomial(15, p=0.5, size=100)
data2 = np.random.binomial(20, p=0.5, size=100)

# Initialize figure
fig = go.Figure()


def ecdf(x):
    x = np.sort(x)
    def result(v):
        return np.searchsorted(x, v, side='right') / x.size
    return result
# Add Traces

fig.add_scatter(x=np.unique(data1), y=ecdf(data1)(np.unique(data1)), name='data1',
                line_shape='hv', line=dict(color="green"))

fig.add_scatter(x=np.unique(data2), y=ecdf(data2)(np.unique(data2)), name='data1',
                line_shape='hv', line=dict(color="blue"))

fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            active=0,
            x=0.57,
            y=1.2,
            buttons=list([
                dict(label="Both",
                     method="update",
                     args=[{"visible": [True, True]},
                           {"title": "Test Plot"}]),
                dict(label="Data1",
                     method="update",
                     args=[{"visible": [True, False]},
                           {"title": "Test Plot"}]),
                dict(label="Data2",
                     method="update",
                     args=[{"visible": [False, True]},
                           {"title": "Test Plot"}]),
            ]),
        )
    ])

# Set title
fig.update_layout(
    title_text="Test Plot",
    xaxis_domain=[0.05, 1.0]
)

fig.show()

fig_out = '/homedirs/man112/access_test/access_inequality_index/figs/test.pdf'

plt.savefig(fig_out,dpi=600,orientation='landscape',format='pdf',facecolor='w', edgecolor='w',transparent=True, bbox_inches="tight")
