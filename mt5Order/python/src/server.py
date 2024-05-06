import socket

print("Hello")

class SocketServer:
    def __init__(self, address='', port=9090):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port
        self.sock.bind((self.address, self.port))
        self.sock.listen(1)
        print("Server is waiting for a connection")
        self.conn, self.addr = self.sock.accept()
        print('Connected to', self.addr)

    def recv_msg(self):
        while True:
            data = self.conn.recv(1024)
            if not data:
                break
            self.conn.sendall(data)  # Echo back to client
            print('Received data:', data.decode("utf-8"))
        
    def __del__(self):
        self.conn.close()
        print('Connection closed')

# serv = SocketServer('127.0.0.1', 9090)
serv = SocketServer('0.0.0.0', 9090)
serv.recv_msg()