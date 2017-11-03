import plotly.graph_objs as go
import plotly.plotly as py
from plotly.graph_objs import *

from config import stream_tokens

# Scatter plot streaming

# Stream definition
plot_holes_stream_token = stream_tokens[-1]
plot_holes_stream_id = go.Stream(token=plot_holes_stream_token)

# Trace
plot_holes_trace = go.Scatter(x=[], y=[], mode='lines+markers', stream=plot_holes_stream_id,
                              marker=Marker(size=12, color='rgb(162, 22, 22)'))

# Layout
plot_holes_layout = go.Layout(title='Plot Holes Detection')

# Figure
plot_holes_fig = go.Figure(data=[plot_holes_trace], layout=plot_holes_layout)

# Plot definition
url_plot_holes = py.plot(plot_holes_fig, filename='box-plots-for-dashboard', auto_open=False, world_readable=True)

# Stream object
plot_hole_stream = py.Stream(plot_holes_stream_token)
