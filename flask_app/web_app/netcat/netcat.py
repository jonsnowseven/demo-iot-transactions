import socket


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
