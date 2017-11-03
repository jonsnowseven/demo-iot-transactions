import sys
import time
import socket
import glob

from pandas import read_csv


class Netcat:
    """ Python 'netcat like' module """

    def __init__(self, ip, port):
        s = socket.socket()
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        host = ip
        port = port

        s.bind((host, port))

        print("Listening on port: %s" % str(port))

        s.listen(5)

        self.socket, addr = s.accept()

    def write(self, data):
        self.socket.send(data.encode('utf-8'))

    def close(self):
        self.socket.close()


def read_all(pattern):
    return glob.glob(pattern)


frequency = float(sys.argv[1])
journey_ids = [int(x) for x in sys.argv[2:]]

transactions = read_all('/Users/joaoneves/Documents/demo-iot-transactions/data/transactions/*.csv')
serialize_rd = lambda x: (','.join((str(i) for i in row)) for row in x.values.tolist())
journey_road_danger = {i + 1: serialize_rd(read_csv(file)) for i, file in enumerate(transactions) if
                       i + 1 in journey_ids}

# print(journey_road_danger)

nc = Netcat(ip='localhost', port=5900)

print(journey_ids)

while True:
    for id in journey_ids:
        try:
            line = next(journey_road_danger[id])
            # print(line)
            nc.write('{}\n'.format(line))
        except Exception as e:
            print(e)
    time.sleep(frequency)

nc.close()
