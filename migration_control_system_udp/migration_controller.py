import threading
import asyncore, socket
import subprocess
import os
import json
import time

class Client(asyncore.dispatcher_with_send):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))
        self.out_buffer = ''

    def handle_close(self):
        self.close()

    def handle_read(self):
        print 'Received', self.recv(1024)
       
    def writable(self):
        return False
    
    def send_msg(self, message):
        print "send:" + message
        sent = self.send(message)


if __name__=="__main__":
    #set up client to connect to sender at salmon
    client_salmon = Client('', 60009)
    client_thread = threading.Thread(target= asyncore.loop)
    client_thread.daemon = True
    client_thread.start()

    #set up client to connect to receiver at luxor
    luxor_client = Client('143.215.131.169', 60011)
    luxor_thread = threading.Thread(target = asyncore.loop)
    luxor_thread.daemon = True
    luxor_thread.start()

    print "Reading configuration file..."
    with open('./configuration.txt', 'r') as in_file:
        expDict = json.load(in_file)
        
        expCount = 0
        for exp in expDict:
            expCount += 1
            print "Experiment ", expCount, " will start in ",exp["before_start_t"],"s:"
            client_salmon.send_msg("start")
            luxor_client.send_msg("start")
            time.sleep(exp["before_start_t"])
            
            print "resume for", exp["start_pause_t"], "s:"
            client_salmon.send_msg("resume")
            luxor_client.send_msg("resume")
            time.sleep(exp["start_pause_t"])

            print "pause for ", exp["pause_resume_t"], "s :"
            client_salmon.send_msg("pause")
            luxor_client.send_msg("pause")
            time.sleep(exp["pause_resume_t"])

            print "resume for ", exp["resume_stop_t"], "s :"
            client_salmon.send_msg("resume")
            luxor_client.send_msg("resume")
            time.sleep(exp["resume_stop_t"])

            print "stop for ", exp["stop_restart_t"], "s :"
            client_salmon.send_msg("stop")
            luxor_client.send_msg("stop")
            time.sleep(exp["stop_restart_t"])        
  
    print "Finish experiments"
    client_salmon.send_msg("exit")
    luxor_client.send_msg("exit")
    print "Program exits"
          
    
