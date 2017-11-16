import plotly.graph_objs as go
import plotly.plotly as py

from config import stream_tokens

pie_stream_id = stream_tokens[-1]
pie_stream = go.Stream(token=pie_stream_id)

transactions_pie_trace = go.Pie(labels=[],
                                values=[],
                                textfont=dict(size=20),
                                hoverinfo='label+percent',
                                textinfo='percent',
                                stream=pie_stream)

transactions_pie_url = py.plot([transactions_pie_trace],
                               filename='Transactions by Location (last period)',
                               fileopt="overwrite",
                               auto_open=False)

transactions_pie_stream = py.Stream(pie_stream_id)
