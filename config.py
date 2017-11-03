import plotly.tools as tls

# username = 'TremandraceaeMolena'
username = 'mari-siemens-demo'
# api_key = 'S0ftNgduow7L9v414nHH'
api_key = 'kUvsbjsdmlZ3crI6J1Vs'
# stream_ids = ["tdt6fc19om", "ad620pd6po", "17jyf65941"]
stream_ids = ["atrk2fsoau", "11xr234is5", "npn2jhd5rz"]
mapbox_access_tokens = [
    # "pk.eyJ1IjoidHJlbWFuZHJhY2VhZW1vbGVuYSIsImEiOiJjajhvaTB0NnowMm5tMzJwM3Bhd2ZqaHdsIn0.OCnZTjAkZf_YVBoYd4f4Mw",
    "pk.eyJ1IjoibWFyaS1zaWVtZW5zLWRlbW8iLCJhIjoiY2o4b3ljYTFqMDduaTJ3bjRxY2M5ZXM5ZSJ9.KMtKH04rjTMONyIHqikEXg",
    "pk.eyJ1IjoibWFyaS1zaWVtZW5zLWRlbW8iLCJhIjoiY2o4b3libnEwMDdkNzJxcDNkbzBvM2FuOSJ9.tGZdsqNkmWyMzhiGi0Ds0A"
    # "pk.eyJ1IjoidHJlbWFuZHJhY2VhZW1vbGVuYSIsImEiOiJjajhvaTI0amYwM2FrMnFwZTJuc2RndmIyIn0.Rxcyq7QBNUy3eiUxSSfHHw"
]
tls.set_credentials_file(username=username, api_key=api_key, stream_ids=stream_ids)
stream_tokens = tls.get_credentials_file()['stream_ids']
