import socket
import sys
import time

class IRC:
 
    irc = socket.socket()
  
    def __init__(self):
        # Deefine the socket
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def command(self,msg):
        self.irc.send(bytes(msg + "\n", "UTF-8"))
 
    def send(self, channel, msg):
        # Transfer data
        self.command("PRIVMSG " + channel + " :" + msg)
 
    def connect(self, server, port, channel, botnick, botpass, botnickpass):
        # Connect to the server
        print("Connecting to: " + server)
        self.irc.connect((server, port))

        # Perform user authentication
        self.command("USER " + botnick + " " + botnick +" " + botnick + " :python")
        self.command("NICK " + botnick)
        #self.irc.send(bytes("NICKSERV IDENTIFY " + botnickpass + " " + botpass + "\n", "UTF-8"))
        time.sleep(5)

        # join the channel
        self.command("JOIN " + channel)
 
    def get_response(self):
        time.sleep(1)
        # Get the response
        resp = self.irc.recv(2040).decode("UTF-8")
 
        if resp.find('PING') != -1:
           self.command('PONG ' + resp.split()[1]  + '\r') 
 
        return resp

def get_query(text: str, botnick: str):
    return text[text.find(botnick) + len(botnick) + 1:]

## IRC Config
server = "irc.libera.chat" 	# Provide a valid server IP/Hostname
port = 6667
channel = "#CSC482"
botnick = "CSC-QA-bot"
botnickpass = ""		# in case you have a registered nickname 		
botpass = ""			# in case you have a registered bot	

irc = IRC()
irc.connect(server, port, channel, botnick, botpass, botnickpass)

while True:
    text = irc.get_response()
    print("RECEIVED ==> ",text) #:foaad-laptop!~foaad-lap@129.65.232.163 PRIVMSG foaad-bot :what's up?

    if "PRIVMSG" in text and channel in text and botnick+":" in text:
        query = get_query(text)
        # answer = answer_question(query)
        answer = "None"
        irc.send(channel, answer)

    if "PRIVMSG" in text and channel in text and botnick+":" in text and "die" in text:
        irc.send(channel, "really? OK, fine.")
        irc.command("QUIT")
        sys.exit()
