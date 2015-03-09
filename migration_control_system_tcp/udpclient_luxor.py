import socket 
import threading
import asyncore
import Queue
import time
import sys
import subprocess
import os
import json

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
class TCPControlServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
	self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(('', port))
        self.listen(1)

    
    def handle_accept(self):
        # when we get a client connection start a dispatcher for that
        # client
        pair = self.accept()
        if pair is None:
            print "self.accept() return null"
            return
        else:
            socket, address = pair
            print 'Connection by', address
            EventHandler(socket)

    def handle_close(self):
        print "Connection closed"
        self.close()


class EventHandler(asyncore.dispatcher_with_send):
    def recv(self, buffer_size):
        print 'test'
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                # a closed connection is indicated by signaling
                # a read condition, and having recv() return 0.
                self.handle_close()
                return ''
            else:
                return data
        except socket.error, why:
            # winsock sometimes throws ENOTCONN
            print why
            print socket.error
            return ''
        

    def handle_read(self):
        
            #sudo = None
	    #sudotcp = None
            msg = self.recv(2456)
            if not msg:
                return
            jsonData = json.loads(msg)
            if jsonData['action'] == "start":
                global expCount
                expCount += 1
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
            if jsonData['action'] == "resume":
                echo = subprocess.Popen(["echo", password],stdout=subprocess.PIPE,)
                sudo = subprocess.Popen(["sudo","-S","iptables","-D","INPUT", "-s", "192.168.9.0/24", "-j", "DROP"],stdin=echo.stdout,stdout=subprocess.PIPE)
                print "resume"
                print sudo.stdout
            if jsonData['action'] == "pause":
                echo = subprocess.Popen(["echo", password],stdout=subprocess.PIPE,)
                sudo = subprocess.Popen(["sudo","-S","iptables","-A","INPUT", "-s", "192.168.9.0/24", "-j", "DROP"],stdin=echo.stdout,stdout=subprocess.PIPE)
                print "pause"
                print sudo.stdout
            if jsonData['action'] == "stop":
                print "stop"
                os.system("sudo kill %d"%(sudotcp.pid))
            if jsonData['action'] == "exit": 
                global q
                q.put(msg)
                sys.exit()

              

if __name__ == "__main__":
   
    #setup tcp server
    tcp_server = TCPControlServer('', 60011)
    tcp_thread = threading.Thread(target=asyncore.loop)
    tcp_thread.daemon = True
    tcp_thread.start()
  
        
    global q
    while(1):
        if not q.empty():
            msg = q.get()
            jsonData = json.loads(msg)
            if jsonData['action'] == "exit":
                print "program exits"
                sys.exit()
    


