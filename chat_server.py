"""
Created on Tue Jul 22 00:47:05 2014

@author: alina, zzhang
"""

import time
import socket
import select
import sys
import string
import indexer
import json
import pickle as pkl
from chat_utils import *
import chat_group as grp
import random


class Server:
    def __init__(self):
        self.new_clients = []  # list of new sockets of which the user id is not known
        self.logged_name2sock = {}  # dictionary mapping username to socket
        self.logged_sock2name = {}  # dict mapping socket to user name
        self.all_sockets = []
        self.group = grp.Group()
        # start server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(SERVER)
        self.server.listen(5)
        self.all_sockets.append(self.server)
        # initialize past chat indices
        self.indices = {}
        # sonnet
        self.sonnet = indexer.PIndex("AllSonnets.txt")
        self.passwords={} #name:password
        self.game_group={} #{1:{"name":"accept","name2":"declined"},2:{}}
        self.snake_color={} #snake color of each player {name:color,...}
        self.colors=["#ff8c00","#00FF00","#03a5fc","#ffc4f5"]# available colors for the snakes
        self.player_status={} #who wins and who loses #{1:{"name":"win","name2":"lost"},2:{}}

    def new_client(self, sock):
        # add to all sockets and to new clients
        print('new client...')
        sock.setblocking(0)
        self.new_clients.append(sock)
        self.all_sockets.append(sock)
    
    def login(self, sock):
        # read the msg that should have login code plus username
        try:
            msg = json.loads(myrecv(sock))
            if len(msg) > 0:
                name=msg["name"]
                print(msg)
                #注册账户        
                if msg["action"]=="register": #create txt files for password saving
                    try:
                        f=open(name + '.txt', 'r')#a string
                        mysend(sock,json.dumps({"action":"register","status":"duplicate"}))
                    except FileNotFoundError:  # user name does not exist, then create one
                        self.passwords[name] = msg["password"]               
                        mysend(sock,json.dumps({"action":"register","status":"ok"}))
                        open(name + '.txt',"w").write(str(msg["password"] ))                
               #登录
                elif msg["action"] == "login":
                    password=msg["password"]
                    
                    #check whether user exist
                    try:
                        self.passwords[name]=open(name + '.txt', 'r').read() #a string
                            #check password correctness
                        if self.passwords[name]!=password:
                            mysend(sock,json.dumps({"action":"login","status":"wrong"})) #wrong password
                        else:
                            #check whether two users log into chat with same account
                            if self.group.is_member(name) != True:
                                # move socket from new clients list to logged clients
                                self.new_clients.remove(sock)
                                # add into the name to sock mapping
                                self.logged_name2sock[name] = sock
                                self.logged_sock2name[sock] = name
                                # load chat history of that user
                                if name not in self.indices.keys():
                                    try:
                                        self.indices[name] = pkl.load(
                                            open(name + '.idx', 'rb'))
                                    except IOError:  # chat index does not exist, then create one
                                        self.indices[name] = indexer.Index(name)
                                print(name + 'logged in')
                                self.group.join(name)
                                mysend(sock, json.dumps(
                                    {"action": "login", "status": "ok"}))
                            else:  # a client under this name has already logged in
                                mysend(sock, json.dumps(
                                    {"action": "login", "status": "duplicate"}))
                                print(name + ' duplicate login attempt')
                    except IOError:            
                        mysend(sock,json.dumps({"action":"login","status":"nonexist"}))# username nonexist, create!
                else:
                    print('wrong code received')
            else:  # client died unexpectedly
                self.logout(sock)
        except Exception as err:
            print(101, err)
            self.all_sockets.remove(sock)

    def logout(self, sock):
        # remove sock from all lists
        name = self.logged_sock2name[sock]
        pkl.dump(self.indices[name], open(name + '.idx', 'wb'))
        del self.indices[name]
        del self.logged_name2sock[name]
        del self.logged_sock2name[sock]
        self.all_sockets.remove(sock)
        self.group.leave(name)
        sock.close()
# ==============================================================================
# main command switchboard
# ==============================================================================
    def handle_msg(self, from_sock):
        # read msg code
        msg = myrecv(from_sock)
        if len(msg) > 0:
            # ==============================================================================
            # handle connect request this is implemented for you
            # ==============================================================================
            msg = json.loads(msg)
            #print("1:"+str(msg))
            if msg["action"] == "connect":
                to_name = msg["target"]
                from_name = self.logged_sock2name[from_sock]
                if to_name == from_name:
                    msg_tosend = json.dumps({"action": "connect", "type":msg["type"],"status": "self"})
                # connect to the peer
                elif self.group.is_member(to_name):
                    to_sock = self.logged_name2sock[to_name]
                    self.group.connect(from_name, to_name)
                    the_guys = self.group.list_me(from_name)
                    msg_tosend = json.dumps(
                        {"action": "connect",  "type":msg["type"],"status": "success"})
                    for g in the_guys[1:]:
                        to_sock = self.logged_name2sock[g]
                        mysend(to_sock, json.dumps(
                            {"action": "connect", "type":msg["type"],"status": "request", "from": from_name})) #peer_msg可以从这里来
                else:
                    msg = json.dumps(
                        {"action": "connect", "status": "no-user"})
                mysend(from_sock, msg_tosend)
# ==============================================================================
# handle messeage exchange: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "exchange":
                from_name = self.logged_sock2name[from_sock]
                #print("2:"+from_name)
                """
                Finding the list of people to send to and index message
                """
                # IMPLEMENTATION
                # ---- start your code ---- #
                message=msg["message"]
                msg_type=msg["type"]
                self.indices[from_name].add_msg_and_index(from_name+": "+message)
                # ---- end of your code --- #
                if msg_type=="secure_chat":  ##change
                    to_sock=self.logged_name2sock[msg["to"]]
                    mysend(to_sock, json.dumps({"action":"exchange",
                                                "from":from_name,"type":msg_type,"message":message}))
                else:
                    the_guys = self.group.list_me(from_name)[1:]
                    #print("3:"+str(the_guys))
                    for g in the_guys:
                        to_sock = self.logged_name2sock[g]
                        self.indices[g].add_msg_and_index(from_name+": "+message)
                        print("from:"+from_name+", type:"+msg_type+", message:"+message)
                        mysend(to_sock, json.dumps({"action":"exchange",
                                                    "from":from_name,"type":msg_type,"message":message})) #peer_msg可以从这里来

# ==============================================================================
# the "from" guy has had enough (talking to "to")!
# ==============================================================================
            elif msg["action"] == "disconnect":
                from_name = self.logged_sock2name[from_sock]
                the_guys = self.group.list_me(from_name)
                self.group.disconnect(from_name)
                the_guys.remove(from_name)
                for g in the_guys:
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action":"exchange",
                                                "from":from_name,"type":"peer_bye"}))
                if len(the_guys) == 1:  # only one left
                    g = the_guys.pop()
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps(
                        {"action": "disconnect", "msg": "everyone left, you are alone"}))#peer_msg可以从这里来
# ==============================================================================
#                 listing available peers: IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "list":

                # IMPLEMENTATION
                # ---- start your code ---- #
                
                msg = str(self.group.list_all())

                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "list", "results": msg}))
# ==============================================================================
#             retrieve a sonnet : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "poem":

                # IMPLEMENTATION
                # ---- start your code ---- #
                poem = self.sonnet.get_poem(int(msg["target"]))
                poem = "\n".join(poem)
                # print('here:\n', poem)
                # ---- end of your code --- #

                mysend(from_sock, json.dumps(
                    {"action": "poem", "results": poem}))
# ==============================================================================
#                 time
# ==============================================================================
            elif msg["action"] == "time":
                ctime = time.strftime('%d.%m.%y,%H:%M', time.localtime())+"\n"
                mysend(from_sock, json.dumps(
                    {"action": "time", "results": ctime}))
# ==============================================================================
#                 search: : IMPLEMENT THIS
# ==============================================================================
            elif msg["action"] == "search":

                # IMPLEMENTATION
                # ---- start your code ---- #
                res=''
                from_name = self.logged_sock2name[from_sock]
                search_rslt = self.indices[from_name].search(msg["target"])

                for t in search_rslt:
                    res=res+t[1]+'\n'
                search_rslt=res
                print('server side search: ' + search_rslt)

                # ---- end of your code --- #
                mysend(from_sock, json.dumps(
                    {"action": "search", "results": search_rslt}))

# ==============================================================================
#                 the game module
# ==============================================================================
            elif msg["action"] == "game": #someone wants game,server发给其他人invitation
                from_name = self.logged_sock2name[from_sock]
                found,group_num=self.group.find_group(from_name) 
                #重置每个游戏组状态
                self.game_group[group_num]={}
                self.player_status[group_num]={}
                print(self.game_group)
                #更改发起人的状态为"Accept"
                self.game_group[group_num][from_name]="Accept"
                the_guys = self.group.list_me(from_name)[1:]
                for g in the_guys:
                    to_sock = self.logged_name2sock[g]
                    mysend(to_sock, json.dumps({"action":"game","from":from_name}))

            elif msg["action"]=="game_response":
                from_name = self.logged_sock2name[from_sock]
                found,group_num=self.group.find_group(from_name) #which group wants to start the game 
                if msg["message"]=="Accept":
                    print("someone accept")
                    self.game_group[group_num][from_name]="Accept"
                elif msg["message"]=="Decline":
                    print("someone decline")
                    self.game_group[group_num][from_name]="Decline"
                self.check_all_response() #if everyone has responded
                        
            #此处收到的msg为:{"action":"snake","coordinate":[[]]}
            elif msg["action"]=="snake":
                from_name = self.logged_sock2name[from_sock]
                coordinate=msg["coordinate"]
                found,group_num=self.group.find_group(from_name)
                for name,status in self.game_group[group_num].items():
                    if status=="Accept" and name !=from_name and self.player_status[group_num][name]=="win":
                        to_sock = self.logged_name2sock[name]
                        color=self.snake_color[from_name]
                        mysend(to_sock, json.dumps({"action":"snake","coordinate":coordinate,"ID":color}))
            
            elif msg["action"]=="food_eaten":
                from_name = self.logged_sock2name[from_sock]
                food_ID=msg["ID"] #是需要delete的food的ID,同时也将是new food的ID
                found,group_num=self.group.find_group(from_name)
                x = random.randint(0, 24) * 20
                y = random.randint(0, 24) * 20
                for name,status in self.game_group[group_num].items():
                    if status=="Accept" and self.player_status[group_num][name]=="win":
                        to_sock = self.logged_name2sock[name]
                        mysend(to_sock, json.dumps({"action":"new_food","coordinate":[x,y],"ID":food_ID}))
            
            elif msg["action"]=="collision": #互相撞 or 撞到边界
                from_name = self.logged_sock2name[from_sock]
                found,group_num=self.group.find_group(from_name)
                loser=msg["loser_ID"] #the color string of the winner
                loser_name= [i for i in self.snake_color if self.snake_color[i]==loser][0]
                self.player_status[group_num][loser_name]="lost"
                print(self.player_status)
                for name,status in self.game_group[group_num].items():
                    if status=="Accept" and name !=from_name: 
                        to_sock = self.logged_name2sock[name]
                        mysend(to_sock, json.dumps({"action":"collision","loser":loser}))
                #check if only one snake left
                count=0
                for k,v in self.player_status[group_num].items():
                    if v=="win":
                        to_sock = self.logged_name2sock[k]
                        count+=1
                        print(count)
                if count==1:
                    mysend(to_sock, json.dumps({"action":"win"}))

        else:
            # client died unexpectedly
            self.logout(from_sock)

# ==============================================================================
# main loop, loops *forever*
# ==============================================================================
    def run(self):
        print('starting server...')
        while(1):
            read, write, error = select.select(self.all_sockets, [], [])
            # print('checking logged clients..')
            for logc in list(self.logged_name2sock.values()):
                if logc in read:
                    self.handle_msg(logc)
            # print('checking new clients..')
            for newc in self.new_clients[:]:
                if newc in read:
                    self.login(newc)
            # print('checking for new connections..')
            if self.server in read:
                # new client request
                sock, address = self.server.accept()
                self.new_client(sock)

    def check_all_response(self):
        #game_group的格式：{1:{"name":"accept","name2":"declined"},2:{}}
        for group_num,group in self.game_group.items():
            if len(group.keys())==len(self.group.chat_grps[group_num]):#if everyone has responded
                #generate food initial position {foodID:[x1,y1],...}
                x1 = random.randint(5, 15) * 20
                y1 = random.randint(5, 15) * 20
                x2 = random.randint(11, 24) * 20
                y2 = random.randint(11, 24) * 20
                pre_x=-1  
                for name,msg in group.items():
                    if msg=="Accept":
                        to_sock = self.logged_name2sock[name]
                        #assign a snake color to each player
                        try:
                            color=self.snake_color[name]
                        except:
                            color=random.choice(self.colors)
                            self.snake_color[name]=color
                            self.colors.remove(color)
                        #assign a unique snake position for each player
                        x=random.randint(0,24)*20
                        while x==pre_x:
                            x=random.randint(0,24)*20
                        pre_x=x
                        #{name1:win,name2:win...} if one dies, sets him to "lost"
                        self.player_status[group_num][name]="win"
                        mysend(to_sock, json.dumps({"action":"start_game","ID":color,"init_Food":{"food1":[x1,y1],"food2":[x2,y2]},"init_snake":[[x,0],[x,20]]}))              

def main():
    server = Server()
    server.run()


if __name__ == '__main__':
    main()
