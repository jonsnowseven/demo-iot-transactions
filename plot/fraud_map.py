import plotly.graph_objs as go
import plotly.plotly as py
from plotly.graph_objs import *

from config import mapbox_access_tokens, stream_tokens

# Maps plot streaming

# Stream definition
maps_stream_token = stream_tokens[-2]
maps_stream_id = go.Stream(token=maps_stream_token, maxpoints=100000)
mapbox_access_token = mapbox_access_tokens[-1]

# Trace
maps_stream_trace = Data([
    Scattermapbox(
        lat=[],
        lon=[],
        mode='markers',
        marker=Marker(
            size=6,
            color='rgb(0, 255, 0)'),
        stream=maps_stream_id
    )
])

# Layout
maps_stream_layout = dict(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=51.5073509,
            lon=-0.12775829999998223
        ),
        pitch=0,
        zoom=6
    )
)

# Figure
maps_stream_fig = dict(data=maps_stream_trace, layout=maps_stream_layout)

# Plot definition
url_maps_stream = py.plot(maps_stream_fig, validate=False, filename="transactions", auto_open=False, fileopt="extend")

# Stream object
maps_stream = py.Stream(maps_stream_token)

