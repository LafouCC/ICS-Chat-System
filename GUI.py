#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 13:36:58 2021

@author: bing
"""

# import all the required  modules
import threading
import select
from tkinter import *
from tkinter import font
from tkinter import ttk
from tkinter import messagebox
from chat_utils import *
import json
from PIL import ImageTk, Image
from snake import *

# GUI class for the chat
class GUI:
    # constructor method
    def __init__(self, send, recv, sm, s):
        # chat window which is currently hidden
        self.Window = Tk()
        self.Window.withdraw()
        self.send = send
        self.recv = recv
        self.sm = sm
        self.socket = s
        self.my_msg = ""
        self.system_msg = ""
        self.showtime=False

    def login(self):
        # login window
        self.login = Toplevel()
        # set the title
        self.login.title("Login")
        self.login.resizable(width = False, 
                             height = False)
        self.login.configure(width = 450,
                             height = 400)
        # create a Label
        self.pls = Label(self.login, 
                       text = "Please login to continue",
                       justify = CENTER, 
                       font = "Helvetica 14 bold")
          
        self.pls.place(relheight = 0.15,
                       relx = 0.2, 
                       rely = 0.07)
        # create a Label for enter user name
        self.label_name = Label(self.login,text = "Name: ",font = "Helvetica 12")
        self.label_name.place(relheight = 0.2,relx = 0.1, rely = 0.2)
        #create a label for enter user password
        self.label_password = Label(self.login,text = "Password: ",font = "Helvetica 12")
        self.label_password.place(relheight = 0.2,relx = 0.1, rely = 0.4)
        
        # tyoing the message
        self.entry_name = Entry(self.login, 
                             font = "Helvetica 14")
          
        self.entry_name.place(relwidth = 0.4, 
                             relheight = 0.12,
                             relx = 0.35,
                             rely = 0.2)
        self.entry_password = Entry(self.login, 
                             font = "Helvetica 14",show="*")
          
        self.entry_password.place(relwidth = 0.4, 
                             relheight = 0.12,
                             relx = 0.35,
                             rely = 0.4)
        # set the focus of the curser
        self.entry_name.focus()
          
        # create a Login Button 
        self.go = Button(self.login,
                         text = "Log In", 
                         font = "Helvetica 14 bold", 
                         height=1,
                         width=7,
                         command = lambda: self.goAhead(self.entry_name.get(),self.entry_password.get()))
        self.go.place(relx = 0.4,
                      rely = 0.65)
        
        # sign up button
        self.reg =Button(self.login,
                         text = "Sign Up", 
                         font = "Helvetica 14 bold",
                         height=1,
                         width=7, 
                         command = self.regUI) 
        self.reg.place(relx=0.4,rely=0.8)

        #picture
        pic1path="assets/1.png"
        image1=ImageTk.PhotoImage(Image.open(pic1path).resize((40,40)))
        self.label_pic1=Label(self.login,image=image1)
        self.label_pic1.place(relx=0.3,rely=0.65)\
        
        pic2path="assets/2.png"
        image2=ImageTk.PhotoImage(Image.open(pic2path).resize((40,25)))
        self.label_pic1=Label(self.login,image=image2)
        self.label_pic1.place(relx=0.3,rely=0.8)

        self.Window.mainloop()
  
    def goAhead(self, name, password):
        if len(name) > 0:
            msg = json.dumps({"action":"login", "name": name,"password":password})# add anohter 键值对
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'nonexist':
                messagebox.showerror("error","User Doesn't Exist")
                return 
            if response["status"] == 'wrong':
                messagebox.showerror("error","Wrong Password")
                return 
            if response["status"] == 'ok':
                self.login.destroy()
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(name)
                self.layout(name)
                self.textCons.config(state = NORMAL)
                self.sm.load_index()
                # self.textCons.insert(END, "hello" +"\n\n")   
                self.textCons.insert(END, menu +"\n\n")      
                self.textCons.config(state = DISABLED)
                self.textCons.see(END)
                # the thread to receive messages
                process = threading.Thread(target=self.proc)
                process.daemon = True
                process.start()
        else:
            messagebox.showerror("error","Username or Password Can't Be Empty")

    def regUI(self):
        self.reg_window=Toplevel()
        self.reg_window.title("Register")
        #the size of the window
        self.reg_window.resizable(width = False, 
                             height = False)
        self.reg_window.configure(width = 400,
                             height = 300)
        self.label1=Label(self.reg_window,text='Name',font = "Helvetica 14")
        self.label2=Label(self.reg_window,text='Password',font = "Helvetica 14")
        self.entry1=Entry(self.reg_window,font = "Helvetica 14")
        self.entry2=Entry(self.reg_window,font = "Helvetica 14",show="*")
        self.label1.place(relx=0.1,rely=0.2)
        self.label2.place(relx=0.1,rely=0.5)
        self.entry1.place(relx=0.35,rely=0.2)
        self.entry2.place(relx=0.35,rely=0.5)
        self.button=Button(self.reg_window,text='Sign Up',font = "Helvetica 14 bold",
                           height=1,
                           width=6,
                           command=lambda:self.register(self.entry1.get(),self.entry2.get()))
        self.button.place(relx=0.4,rely=0.7)

    def register(self,name,password):
        if name==''or password=='':
            messagebox.showerror("error",'Invalid Input')
            return
        else:
            msg=json.dumps({"action":"register","name":name,"password":password})
            self.send(msg)
            response=json.loads(self.recv())
            if response["status"]=="duplicate":
                messagebox.showerror('error','Username Already Exists')
                return
            elif response["status"]=='ok':
                messagebox.showinfo(None,'Register Successful')
                self.reg_window.destroy()

    # The main layout of the chat
    def layout(self,name):
        self.name = name
        # to show chat window
        self.Window.deiconify()
        self.Window.title("CHATROOM")
        self.Window.resizable(width = False,
                              height = False)
        self.Window.configure(width = 560,
                              height = 620,
                              bg = "#17202A")
        self.labelHead = Label(self.Window,
                             bg = "#17202A", 
                              fg = "#EAECEE",
                              text = self.name ,
                               font = "Helvetica 15 bold",
                               pady = 5)
          
        self.labelHead.place(relwidth = 1)
        self.line = Label(self.Window,
                          width = 450,
                          bg = "#ABB2B9")
          
        self.line.place(relwidth = 1,
                        rely = 0.07,
                        relheight = 0.012)
        #the text box
        self.textCons = Text(self.Window,
                             bg = "#17202A",
                             fg = "#EAECEE",
                             font = "Helvetica 14", 
                             padx = 5,
                             pady = 5)
          
        self.textCons.place(relheight = 0.8,
                            relwidth = 0.97, 
                            rely = 0.08)
        self.textCons.config(state = DISABLED) 
        self.textCons.config(cursor = "arrow")

        self.labelBottom = Label(self.Window,
                                 bg = "#ABB2B9",
                                 height = 60)
          
        self.labelBottom.place(relwidth = 1,
                               rely = 0.88,)
        #input entry
        self.entryMsg = Entry(self.labelBottom,
                              bg = "#2C3E50",
                              fg = "#EAECEE",
                              font = "Helvetica 13")
        self.entryMsg.place(relwidth = 0.64,
                            relheight = 0.045,
                            rely = 0.008,
                            relx = 0.011)    
        self.entryMsg.focus()

        self.entryMsg.bind("<Return>", self.enter_msg) 
        # create a Send Button
        self.buttonMsg = Button(self.labelBottom,
                                text = "Send",
                                font = "Helvetica 10 bold",
                                bg = "#ABB2B9",
                                command = lambda : self.sendButton(self.entryMsg.get()))
          
        self.buttonMsg.place(relx = 0.67,
                             rely = 0.008,
                             relheight = 0.045, 
                             relwidth = 0.1)
        self.button_game=Button(self.labelBottom,text="Time",
                                font = "Helvetica 10 bold",
                                bg = "#ABB2B9",
                                command=lambda:self.time())
        
        self.button_game.place(relx = 0.8,
                                rely = 0.008,
                                relheight = 0.045, 
                                relwidth = 0.1)
        # create a scroll bar
        scrollbar = Scrollbar(self.Window)
        scrollbar.place(relheight = 0.8,rely=0.08,relx = 0.97)  
        scrollbar.config(command = self.textCons.yview)

    def enter_msg(self,event):
        self.sendButton(self.entryMsg.get())
        
    # function to basically start the thread for sending messages
    def sendButton(self, msg):
        self.textCons.config(state = DISABLED)
        self.my_msg = msg
        self.entryMsg.delete(0, END)
    
    def time(self):
        self.showtime=True

    def proc(self):
        while True:
            read, write, error = select.select([self.socket], [], [], 0)
            peer_msg = []
            # print(self.msg)
            if self.socket in read:
                peer_msg = self.recv()
            if self.showtime:
                    self.my_msg="time"
                    self.showtime=False
            if len(self.my_msg) > 0 or len(peer_msg) > 0:
                self.system_msg = self.sm.proc(self.my_msg, peer_msg)
                self.my_msg = ""
                if len(self.system_msg)>0:  
                    self.textCons.config(state = NORMAL)
                    # print(self.system_msg)
                    self.textCons.insert(END, self.system_msg )     
                    self.textCons.config(state = DISABLED)
                    self.textCons.see(END)


    def run(self):
        self.login()
# create a GUI class object
if __name__ == "__main__": 
    g = GUI()