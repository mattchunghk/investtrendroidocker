import socket
print("Hello")
class socketserver:
    def __init__(self, address = '', port = 9090):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = address
        self.port = port
        self.sock.bind((self.address, self.port))
        self.cummdata = ''
    def waitforconnection(self):
        self.sock.listen(1)
        self.conn, self.addr = self.sock.accept()
        print('connected to', self.addr)
        return 1

    def recvmsg(self):
        self.cummdata = ''
        while True:
            data = self.conn.recv(10000)
            self.cummdata+=data.decode("utf-8")
            if not data:
                break    

            self.conn.send(bytes(self.cummdata,"utf-8")) # loop back test

            return self.cummdata
   
    def __del__(self):
        print('sock close')
        self.sock.close()

#####################################################

# serv = socketserver('192.168.128.74', 9090)
# serv = socketserver('0.0.0.0', 9090)
serv = socketserver('127.0.0.1', 9090)
# serv = socketserver('124.244.251.203', 9090)
print("server Waiting for the connection")
serv.waitforconnection()

while True: 
    msg = serv.recvmsg()
    
    print('received data : ',msg);