import socket
import threading
import asyncore, socket
import Queue
import time
import os
import sys
import subprocess
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import json

q = Queue.Queue()
password = "19910428" ## replace password in the "PASSWORD"
clients = []
class WSHandler(tornado.websocket.WebSocketHandler):
   
    def check_origin(self,origin):
        return True

    def open(self):
        print 'new connection'
        global clients
        clients.append(self)
      
    def on_message(self, message):
        print 'message received %s' % message
 
    def on_close(self):
      print 'connection closed'
      clients.remove(self)

def write_to_clients(msg):
    print 'writing to clients'
    for client in clients:
        print 'client'
        client.write_message(msg)
 
 
application = tornado.web.Application([
    (r'/ws', WSHandler),
])



#-----------------------------------------------
# Server Class: receive msg from controller
#----------------------------------------------
class TCPServer(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind(('', port))
        self.listen(1)

    def handle_accept(self):
        # when we get a client connection start a dispatcher for that
        # client
        pair  = self.accept()
        if pair is not None:
            socket, address = pair
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
        
        pktLossFilePath = './pkt_loss/pkt_loss_without_pause.txt'
        with open(pktLossFilePath, 'w') as pktLossFile:
            pause = True
            expCount = 0;
            sudo = None
            jsonData = json.loads(msg)
            if jsonData["action"] == "start":
                expCount += 1
                print "Experiment:", expCount
                pktLossFile.write('Experiment '+str(expCount) + '\n')
                tcpdump_file_dir = "./tcpdump/tcpdumpresult_"+str(expCount)+".pcap"
                #start tcpdump
                echo = subprocess.Popen(["echo", password],stdout=subprocess.PIPE,)
                sudo = subprocess.Popen(["sudo","-S","tcpdump","-i","eth2", "host", "192.168.9.2", "and", "192.168.9.3", "-w", tcpdump_file_dir],stdin=echo.stdout,stdout=subprocess.PIPE)
                print sudo.stdout
                #send message to dash to notify migration
                if 'pause_after' in jsonData:
                    pause_time = jsonData['pause_after']
                    print 'pause_time:',pause_time                      
                    if 'pause_duration' in jsonData:                             
                        pause_duration = jsonData['pause_duration']
                        print 'pause duration:',pause_duration
                        msg = {"action":'pause',"pause_time":pause_time, "pause_duration":pause_duration}
                        write_to_clients(json.dumps(msg))
            if jsonData["action"] == "stop":
                #stop tcpdump
                os.system("sudo kill %d"%(sudo.pid))
            if jsonData["action"] == "pause":
                #pause = True	       #for pausing the application
                pause = False	#for no pausing the application (base line case)
            if jsonData["action"] == "resume":
                pause = False
                msg = {"action":"resume"}
                write_to_clients(json.dumps(msg))
            if jsonData['action'] == "exit":
                sys.exit()
                

if __name__ == "__main__":

   
    #start listening to controller
    s = TCPServer('', 60009)
    server_thread = threading.Thread(target=asyncore.loop)
    server_thread.daemon = True
    server_thread.start()
  
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
   
    
    
    server_thread.join()
   
