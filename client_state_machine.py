"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
import json
from tkinter import *
from snake import *
import threading
import pickle as pk
import indexer
import os

class ClientSM:
    def __init__(self, s):
        self.state = S_OFFLINE
        self.peer = ''
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.game_res=False #whether I am accepting the game invitation
        self.if_private=0
        self.peer_pub_key={}#PUBLIC_KEY ##change

    def __del__(self):
        #print("3:"+self.me + '_local.idx')
        pk.dump(self.logging, open(self.me + '_local.idx','wb'))

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer,chatting_type):
        msg = json.dumps({"action":"connect", "type":chatting_type,"target":peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            self.peer = peer
            self.out_msg += 'You are connected with '+ self.peer + '\n'
            return (True)
        elif response["status"] == "busy":
            self.out_msg += 'User is busy. Please try again later\n'
        elif response["status"] == "self":
            self.out_msg += 'Cannot talk to yourself (sick)\n'
        else:
            self.out_msg += 'User is not online, try again later\n'
        return(False)

    def disconnect(self):
        msg = json.dumps({"action":"disconnect"})
        mysend(self.s, msg)
        self.out_msg += 'You are disconnected from ' + self.peer + '\n'
        self.peer = ''
    
    def game_init(self,color,food_info,snake_init):
        self.game_window=Toplevel() 
        self.game_canvas=Canvas(self.game_window,bg=BACKGROUND, height=HEIGHT, width=WIDTH)
        self.game_label=Label(self.game_window,text="Points:{}".format(0), font=('consolas', 20))
        self.game = Game(self.game_window,self.game_label,self.game_canvas,self.s,color,snake_init)
        process=threading.Thread(target=lambda:self.game.run(food_info))
        process.daemon = True
        process.start()
        
    
    def send_my_public_key(self):
        if self.if_private==1:
            my_public_key=base64.b64encode(PUBLIC_KEY).decode()
            #print(my_public_key)
            #sending_message="__exchange_pub_key__:"+my_public_key
            #mysend(self.s,json.dumps({"action":"excahnge","from":"["+self.me+"]","type":"key","message":my_public_key}))
            mysend(self.s,json.dumps({"action":"exchange","from":"["+self.me+"]","type":"key","message":my_public_key}))

    def load_index(self): ##change
        #print(self.me+"_local.idx")
        file_name=self.me+"_local.idx"
        try:
            if os.stat(file_name).st_size > 0:
               self.logging=pk.load(open(file_name,"rb"))
            else:
               self.logging=indexer.Index(self.me+"_local")
        except IOError:
            self.logging=indexer.Index(self.me+"_local")

    def save_chat_locally(self,msg,from_user): ##change
        try:
            self.logging.add_msg_and_index(text_proc(msg,from_user)) 
        except:
            self.load_index()

    def search_hist(self,term): ##change
        search_result="\n".join([x[-1]+"\n" for x in self.logging.search(term)])        
        return search_result
    
    def proc(self, my_msg, peer_msg):
        self.out_msg = ''
#==============================================================================
# Once logged in, do a few things: get peer listing, connect, search
# And, of course, if you are so bored, just go
# This is event handling instate "S_LOGGEDIN"
#==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:
                
                if my_msg == 'q':
                    self.out_msg += 'See you next time!\n'
                    self.state = S_OFFLINE
                    try:
                        #pk.dumps(self.logging,open(self.me+"_local.idx",'wb'))
                        pk.dump(self.logging,open(self.me+"_local.idx",'wb'))
                    except:
                        pass

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action":"list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg +='Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c' or my_msg[0:2]=="sc":
                    if my_msg[0] == 'c':
                        peer=my_msg[1:]
                        chatting_type="normal"
                    else:
                        peer = my_msg[2:]
                        chatting_type="secure"
                    peer = peer.strip()
                    
                    if self.connect_to(peer,chatting_type) == True:
                        self.state = S_CHATTING
                        self.if_private=0
                        if my_msg[0:2]=="sc":
                            self.if_private=1
                            self.send_my_public_key()  
                            self.out_msg+="Securely chat with your peers!\n"
                            self.out_msg+='-----------------------------------\n'                     
                        # self.out_msg += 'Connect to ' + peer + '\n' ##need to change
                        elif my_msg[0]=="c":
                            self.out_msg +="Simply chat or type 'game' to invite others to Snake game!\n"
                            self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful\n\n'

                elif my_msg[0] == '?': #search chat history from local file
                    search_rslt=self.search_hist(my_msg[1:].strip())
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n\n'
                    else:
                        self.out_msg += '\'' + my_msg[1:] + '\'' + ' not found\n\n'

                elif my_msg[0] == 'p' and my_msg[1:].isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action":"poem", "target":poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if (len(poem) > 0):
                        self.out_msg += poem + '\n\n'
                    else:
                        self.out_msg += 'Sonnet ' + poem_idx + ' not found\n\n'

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.peer = peer_msg["from"]
                    self.out_msg += 'Request from ' + self.peer + '\n'
                    self.out_msg += '------------------------------------\n\n'
                    self.out_msg += 'You are connected with ' + self.peer+"\n"
                    self.state = S_CHATTING
                    #print(peer_msg)
                    self.if_private=0
                    if peer_msg["type"]=="secure":
                        self.if_private=1
                        self.send_my_public_key()
                        self.out_msg+="Securely chat with your peers!\n"
                        self.out_msg+='-----------------------------------\n'
                    elif peer_msg["type"]=="normal":
                        self.out_msg += "Simply chat or type 'game' to invite others to Snake game!\n"
                        self.out_msg += '------------------------------------\n'
                        #print("connect by others")
                        


#==============================================================================
# Start chatting, 'bye' for quit
# This is event handling instate "S_CHATTING"
#==============================================================================
        elif self.state == S_CHATTING:  
            self.out_msg=""
            if len(my_msg) > 0:     # my stuff going out
                self.save_chat_locally(my_msg,self.me)
                self.out_msg=self.me+": "+my_msg+"\n\n"
                if my_msg=="time":
                    self.out_msg=""
                    mysend(self.s, json.dumps({"action":"time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "Time is: " + time_in
                elif self.peer_pub_key!={}:
                    for name,key in self.peer_pub_key.items():        ##change             
                        current_sending_msg=myencrypt(my_msg,key,self.if_private)
                        mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "to":name,"type":"secure_chat","message":current_sending_msg}))
                else:
                    mysend(self.s, json.dumps({"action":"exchange", "from":"[" + self.me + "]", "type":"chat","message":my_msg}))
                if my_msg == 'bye':
                    self.disconnect()
                    self.state = S_LOGGEDIN
                    self.peer = ''
                    self.peer_pub_key={}                    
                #me start game
                elif my_msg.lower()=="game":
                    mysend(self.s, json.dumps({"action":"game", "from":"[" + self.me + "]"}))
                #判断实在chat还是在respond to invitation
                elif self.game_res==True:
                    if my_msg.strip(" ").lower()=='accept':
                        mysend(self.s, json.dumps({"action":"game_response", "from":"[" + self.me + "]", "message":"Accept"}))
                        self.game_res=False
                    elif my_msg.strip(" ").lower()=='decline':
                        mysend(self.s, json.dumps({"action":"game_response", "from":"[" + self.me + "]", "message":"Decline"}))   
                        self.game_res=False
                    else:
                        self.out_msg +="Invalid Response"+"\n"

            if len(peer_msg) > 0:    # peer's stuff, coming in
                peer_msg = json.loads(peer_msg)
                if peer_msg["action"] == "connect":
                    self.out_msg += "(" + peer_msg["from"] + " joined)\n"
                    self.peer+= " "+peer_msg['from']
                    self.send_my_public_key() ##change
                elif peer_msg["action"] == "disconnect":
                    self.state = S_LOGGEDIN
                    #del self.peer_pub_key[peer_msg["from"]] ##change
                elif peer_msg["action"]=="exchange":
                    if peer_msg["type"]=="key":
                        #print(peer_msg["message"])
                        self.peer_pub_key[peer_msg["from"]]=base64.b64decode(peer_msg["message"].encode()) ##change
                        #print(self.peer_pub_key.decode())
                    elif peer_msg["type"]=="peer_bye":
                        try:
                            del self.peer_pub_key[peer_msg["from"]] ##change
                        except:
                            pass
                    else:
                        #print(peer_msg)
                        receive_msg=mydecrypt(peer_msg["message"],self.if_private)
                        self.save_chat_locally(receive_msg,peer_msg["from"])
                        self.out_msg += peer_msg["from"] +': ' + receive_msg+"\n\n"
                        #store

                #other invite me to game
                elif peer_msg["action"]=="game":
                    self.out_msg +=peer_msg["from"]+" invite you to play game\n"
                    self.out_msg +="type 'Accept' or 'Decline'\n\n"
                    self.game_res=True

                #everyone has responded invitation, time to start
                elif peer_msg["action"]=="start_game":
                    color=peer_msg['ID']
                    food_info=peer_msg["init_Food"] 
                    snake_init=peer_msg["init_snake"]
                    self.game_init(color,food_info,snake_init) #only one window will pop up for one user
                
                #below is the info reveiced during gaimng
                elif peer_msg["action"]=="snake": #other snake coming in
                    coordinate=peer_msg["coordinate"] 
                    color=peer_msg["ID"] #it is a string of hex color e.g."#ff8c00"
                    self.game.peer_snake(coordinate,color)
                
                elif peer_msg["action"]=="new_food" and self.game.end==False:
                    coordinate=peer_msg["coordinate"]
                    food_ID=peer_msg["ID"]
                    self.game.food_change(coordinate,food_ID)
                
                elif peer_msg["action"]=="collision":
                    loser=peer_msg["loser"]
                    self.game.delete_loser(loser)
                
                elif peer_msg["action"]=="win":
                    self.game.win()

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu+"\n"
        
#==============================================================================
# invalid state
#==============================================================================        
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)
        
        return self.out_msg
        