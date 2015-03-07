import socket
import threading
import asyncore, socket
import Queue
import time
import os
import sys
import subprocess

q = Queue.Queue()
password = "19910428" ## replace password in the "PASSWORD"

#-----------------------------------------------
# UDP Client Class: send msg to udp server
#----------------------------------------------

class UdpClient(asyncore.dispatcher_with_send):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.server = host
        self.port = port
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        pktLossFilePath = './pkt_loss/pkt_loss_without_pause.txt'
        with open(pktLossFilePath, 'w') as pktLossFile:
            pause = True
            pktCount=0
            expCount = 0;
            sudo = None
            while(1):            
                #check if pause 
                global q
                if not q.empty():
                    msg = q.get()
                    print msg
                    if msg == "start":
                        expCount += 1
                        pktCount = 0
                        print "Experiment:", expCount
                        pktLossFile.write('Experiment '+str(expCount) + '\n')
                        tcpdump_file_dir = "./tcpdump/tcpdumpresult_"+str(expCount)+".pcap"
                        #start tcpdump
                        echo = subprocess.Popen(["echo", password],stdout=subprocess.PIPE,)
                        sudo = subprocess.Popen(["sudo","-S","tcpdump","-i","eth2", "host", "192.168.9.2", "and", "192.168.9.3", "-w", tcpdump_file_dir],stdin=echo.stdout,stdout=subprocess.PIPE)
                        print sudo.stdout
                    if msg == "stop":
                        #stop tcpdump
                        os.system("sudo kill %d"%(sudo.pid))
                        print "pkt sent:", pktCount
                        pktLossFile.write('Number of pkts sent: ' + str(pktCount) + '\n')
                    if msg == "pause":
                        #pause = True	       #for pausing the application
                        pause = False	#for no pausing the application (base line case)
                    if msg == "resume":
                        pause = False
                    if msg == "exit":
                        sys.exit()
                elif not pause:
                    pktCount += 1
                    #print "send ",pktCount," msg"
                    msg = (str(pktCount)+ "###" + str(time.time()) + "###"+ os.urandom(1400).encode('hex'))[:1400]
                    self.send_msg(msg)
                    time.sleep(0.02)
                    
 

    def handle_close(self):
        self.close()

    def handle_read(self):
        print 'Received', self.recvfrom(1024)
       
    def writable(self):
        return False
    
    def send_msg(self, message):
        sent = self.sendto(message, (self.server, self.port))


#-----------------------------------------------
# Server Class: receive msg from controller
#----------------------------------------------
class Server(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
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
        msg = self.recv(8192)
        if not msg:
            return

        print "receive msg: ",msg
             
        global q
        q.put(msg)

  

if __name__ == "__main__":

   
    #start listening to controller
    s = Server('', 60009)
    server_thread = threading.Thread(target=asyncore.loop)
    server_thread.daemon = True
    server_thread.start()
  
    #setup udp client
    client = UdpClient('192.168.9.2', 60010)
    client_thread = threading.Thread(target=asyncore.loop)
    client_thread.daemon = True
    client_thread.start()
    
    server_thread.join()
   
