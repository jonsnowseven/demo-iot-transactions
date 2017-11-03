import re

import plotly.dashboard_objs as dashboard
import plotly.graph_objs as go
import plotly.plotly as py
from plotly.graph_objs import *
from plot.fraud_map import url_maps_stream
from plot.g_force_plot import url_plot_holes

from config import username


def file_id_from_url(url):
    """Return fileId from a url."""
    match = re.search(r"~{}\/(?P<id>\d+)".format(username), url)
    if match:
        return username + ":" + match.group("id")


# fieldIdPlot = file_id_from_url(url_plot_holes)
fieldIdMap = file_id_from_url(url_maps_stream)

# box_a = {
#     'type': 'box',
#     'boxType': 'plot',
#     'fileId': fieldIdPlot,
#     'title': 'Plot Holes'
# }

box_c = {
    'type': 'box',
    'boxType': 'plot',
    'fileId': fieldIdMap,
    'title': 'Fraud Detection Map',
}

dashboard_name = 'Fraud Detection Dashboard'


def upload_dashboard():
    recent_dashboards = py.dashboard_ops.get_dashboard_names()

    if dashboard_name not in recent_dashboards:
        dboard = dashboard.Dashboard()
        # Insert boxes
        dboard.insert(box_c)
        # dboard.insert(box_a)
        # dboard.insert(box_c, 'right', 1)
        # Insert title
        dboard['settings']['title'] = dashboard_name
        # dboard['layout']['size'] = 3000
        dboard['settings']['foregroundColor'] = '#000000'
        dboard['settings']['backgroundColor'] = '#adcaea'
        dboard['settings']['headerForegroundColor'] = '#ffffff'
        dboard['settings']['headerBackgroundColor'] = '#008fb3'
        dboard['settings']['boxBackgroundColor'] = '#ffffff'
        dboard['settings']['boxBorderColor'] = '#000000'
        dboard['settings']['boxHeaderBackgroundColor'] = '#ffffff'
        # Upload dashboard
        dashboard_url = py.dashboard_ops.upload(dboard, dashboard_name)
        return dashboard_url
    else:
        return py.dashboard_ops.get_dashboard(dashboard_name)
