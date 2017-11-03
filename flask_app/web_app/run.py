import time

from web_app.netcat.netcat import Netcat
from web_app.utils.recipes import read_all


from pandas import read_csv

# path = '/Users/joaoneves/Documents/demo-siemens/data/g_force_journeys/*.csv'
path = '/Users/joaoneves/Documents/demo-siemens/data/journeys/*.csv'
files = read_all(path)

serialize = lambda x: [','.join([str(i) for i in row[1:-1]]) for row in x.values.tolist()]
# serialize = lambda x: [','.join([str(i) for i in row]) for row in x.values.tolist()]

journeys = [serialize(read_csv(file)) for file in files]

nc = Netcat(ip='localhost', port=5900)
# nc = Netcat(ip='localhost', port=5901)

for journey in journeys:

    for row in journey:
        time.sleep(0.5)
        nc.write('{}\n'.format(row))

nc.close()
