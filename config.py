import plotly.tools as tls

username = 'm-iot-transactions'
api_key = 'w6sZmOJN7WpEg767Cz5V'
stream_ids = ["7f1r9f7kwx", "hlhsuj7pyu"]
mapbox_access_tokens = [
    "pk.eyJ1IjoibS1pb3QtdHJhbnNhY3Rpb25zIiwiYSI6ImNqYTJqNjZuaDh5eGcycXFzeDlwMDhsZG8ifQ.sBCXyy-RYSnznknB1QikVg",
    "pk.eyJ1IjoibS1pb3QtdHJhbnNhY3Rpb25zIiwiYSI6ImNqYTJqM3IwMTV6ejgycG12anJzdG52dTYifQ.jLeHCjv9EqR80ctlVRYHTg"
]
tls.set_credentials_file(username=username, api_key=api_key, stream_ids=stream_ids)
stream_tokens = tls.get_credentials_file()['stream_ids']
