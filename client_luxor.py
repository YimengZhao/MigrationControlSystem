import socket 
import threading
import asyncore
import Queue
import time
import sys
import subprocess
import os

q = Queue.Queue()
global recvPktCount
recvPktCount = 0
global sudotcp
sudotcp = None
global pktLossFile
pktLossFile = open("./pkt_loss/pkt_loss_without_pause.txt", 'w')
global expCount
expCount = 0

password = "19910428" #replace password
#-----------------------------------------------
# Server Class: receive msg from controller
#----------------------------------------------
class TCPServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
	self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(('', port))
        self.listen(1)

        
        

    def handle_accept(self):
        # when we get a client connection start a dispatcher for that
        # client
        socket, address = self.accept()
        print 'Connection by', address
        EventHandler(socket)

    def handle_close(self):
        print "Connection closed"
        self.close()


class EventHandler(asyncore.dispatcher_with_send):
 
    def handle_read(self):
        
            #sudo = None
	    #sudotcp = None
            msg = self.recv(8192)
            if not msg:
                return
            if msg == "start":
                global expCount
                expCount += 1
                global recvPktCount
                recvPktCount = 0
                print 'Experiment: ',expCount
                global pktLossFile
                pktLossFile.write('Experiment: ' + str(expCount) + '\n')
                pktLossFile.flush()
                tcpdump_file_dir = "./tcpdump/tcpdumpresult_"+str(expCount)+".pcap"
                #start tcpdump
                echo = subprocess.Popen(["echo", password],stdout=subprocess.PIPE,)
                global sudotcp
                sudotcp = subprocess.Popen(["sudo","-S","tcpdump","-i","eth1", "host", "192.168.9.2", "and", "192.168.9.3", "-w", tcpdump_file_dir],stdin=echo.stdout,stdout=subprocess.PIPE)
                print sudotcp.stdout
                print "start"
            if msg == "resume":
                echo = subprocess.Popen(["echo", password],stdout=subprocess.PIPE,)
                sudo = subprocess.Popen(["sudo","-S","iptables","-D","INPUT", "-s", "192.168.9.0/24", "-j", "DROP"],stdin=echo.stdout,stdout=subprocess.PIPE)
                print "resume"
                print sudo.stdout
            if msg == "pause":
                echo = subprocess.Popen(["echo", password],stdout=subprocess.PIPE,)
                sudo = subprocess.Popen(["sudo","-S","iptables","-A","INPUT", "-s", "192.168.9.0/24", "-j", "DROP"],stdin=echo.stdout,stdout=subprocess.PIPE)
                print "pause"
                print sudo.stdout
            if msg == "stop":
                print "stop"
                global recvPktCount
                print "Received Pkt: ", recvPktCount
                global pktLossFile
                pktLossFile.write("Received Pkt:" + str(recvPktCount) + '\n')
                pktLossFile.flush()
                
                recvPktCount = 0
                os.system("sudo kill %d"%(sudotcp.pid))
            if msg == "exit": 
                global q
                q.put(msg)
                sys.exit()

#-----------------------------------------------
# A simple UDP server
#----------------------------------------------
class UdpServer(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)
        self.server = host
        self.port = port
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((host,port))

        print "The server is ready to receive"
        global recvPktCount
        recvPktCount = 0
        while(1):
            message, clientAddress = server_socket.recvfrom(2456)
            recvPktCount += 1                

    


if __name__ == "__main__":
   
    #setup tcp server
    tcp_server = TCPServer('', 60011)
    tcp_thread = threading.Thread(target=asyncore.loop)
    tcp_thread.daemon = True
    tcp_thread.start()
  
    #setup udp server
    udp_server = UdpServer('192.168.9.2', 60010)
    udp_server.daemon = True
    udp_server.start()
    
    global q
    while(1):
        if not q.empty():
            msg = q.get()
            if msg == "exit":
                print "program exits"
                sys.exit()
    


