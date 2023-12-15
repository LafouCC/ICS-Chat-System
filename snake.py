# Program in Python to create a Snake Game 
from chat_utils import *
import tkinter as tk
import random 
import json

WIDTH = 500
HEIGHT = 500
SPEED = 300
SPACE_SIZE = 20
BODY_SIZE = 2
# SNAKE = "#00FF00"
FOOD = "#FFFFFF"
BACKGROUND = "#000000"

# Class to design the snake 
class Snake: 
    def __init__(self, canvas,coordinates,color): #use color to be the tag of squares
        self.body_size = BODY_SIZE 
        self.coordinates = coordinates
        self.squares = []
        self.color=color 

        for x, y in self.coordinates: 
            square = canvas.create_rectangle( 
				x, y, x + SPACE_SIZE, y + SPACE_SIZE, 
					fill=self.color, tag=self.color) 
            self.squares.append(square)

class Food: 
    def __init__(self, canvas,coordinates,ID):
        self.ID=str(ID) #a string e.g. "1"
        self.canvas=canvas
        self.coordinates = coordinates
    def show(self):
        x=self.coordinates[0]
        y=self.coordinates[1]
        self.canvas.create_oval(x, y, x + SPACE_SIZE, y +
						SPACE_SIZE, fill=FOOD, tag=self.ID)
    def delete(self):
        self.canvas.delete(self.ID) 

class Game:
    def __init__(self, window, label, canvas, socket,ID,snake_init):
        # super().__init__()
        self.score = 0
        self.direction = 'down'
        self.window = window
        self.label = label
        self.canvas = canvas
        self.socket=socket # the player's socket
        self.color=ID
        #initialize self snake
        self.snake = Snake(self.canvas,snake_init,ID)
        self.end=False 

    # Function to check the next move of snake 
    def next_turn(self):
        if self.end==False: 
            x, y = self.snake.coordinates[0] 
            if self.direction == "up": 
                y -= SPACE_SIZE 
            elif self.direction == "down": 
                y += SPACE_SIZE 
            elif self.direction == "left": 
                x -= SPACE_SIZE 
            elif self.direction == "right": 
                x += SPACE_SIZE 

            self.snake.coordinates.insert(0, (x, y)) 
            if self.end==False:
                square = self.canvas.create_rectangle( 
                    x, y, x + SPACE_SIZE, 
                            y + SPACE_SIZE, fill=self.color) 
            self.snake.squares.insert(0, square) 

            #self.food is a list: [Food(),Food()]
            eat=False
            for food in self.food[::-1]:
                if x == food.coordinates[0] and y == food.coordinates[1]:
                    self.score += 1
                    self.label.config(text="Points:{}".format(self.score)) 
                    mysend(self.socket,json.dumps({"action":"food_eaten","ID":food.ID})) #send the food1 as eaten
                    food.delete()
                    self.food.remove(food)
                    eat=True
            if not eat: 
                del self.snake.coordinates[-1] 
                self.canvas.delete(self.snake.squares[-1]) 
                del self.snake.squares[-1] 
                mysend(self.socket,json.dumps({"action":"snake","coordinate":self.snake.coordinates})) #send the coordinates of the snake
            
            if self.check_collisions(self.snake):
                self.end=True
                mysend(self.socket,json.dumps({"action":"collision","loser_ID":self.color}))  
                self.game_over()
            else:
                self.window.after(SPEED, self.next_turn) 

    # Function to control direction of snake 
    def change_direction(self, new_direction): 

        # global direction 

        if new_direction == 'left': 
            if self.direction != 'right': 
                self.direction = new_direction 
        elif new_direction == 'right': 
            if self.direction != 'left': 
                self.direction = new_direction 
        elif new_direction == 'up': 
            if self.direction != 'down': 
                self.direction = new_direction 
        elif new_direction == 'down': 
            if self.direction != 'up': 
                self.direction = new_direction 

    # function to check snake's collision and position 
    def check_collisions(self, snake): 

        x, y = snake.coordinates[0] 

        if x < 0 or x >= WIDTH: 
            return True
        elif y < 0 or y >= HEIGHT: 
            return True

        for body_part in snake.coordinates[1:]: 
            if x == body_part[0] and y == body_part[1]: 
                return True

        return False

    # Function to control everything 
    def game_over(self): 
        print("gameover")
        self.canvas.delete("all")
        self.canvas.delete(tk.ALL)
        time.sleep(0.5)
        self.canvas.create_rectangle(0,0,500,500,fill="#000000")
        self.canvas.create_text(self.canvas.winfo_width()/2, 
                        self.canvas.winfo_height()/2, 
                        font=('consolas', 70), 
                        text="YOU LOST", fill="red", 
                        tag="gameover") 
    
    # functions I created
    def peer_snake(self,coordinate,color):
        try:
            self.canvas.delete(color)
        except:
            pass
        if self.end==False:
            for x, y in coordinate:
                if self.end==True:
                    break 
                self.canvas.create_rectangle( 
                    x, y, x + SPACE_SIZE, y + SPACE_SIZE, 
                        fill=color, tag=color)
                # check if I bump into other snakes
                for my_x,my_y in self.snake.coordinates:
                    if my_x==x and my_y==y:
                        if len(self.snake.coordinates)==len(coordinate):
                            pass
                        elif len(self.snake.coordinates)<len(coordinate):
                            self.end=True
                            self.game_over()
                            mysend(self.socket,json.dumps({"action":"collision","loser_ID":self.color}))
                        elif len(self.snake.coordinates)>len(coordinate):
                            mysend(self.socket,json.dumps({"action":"collision","loser_ID":color}))
                   
                        

    def food_change(self,coordinate,ID):
        if self.food:
            for food in self.food:
                if food.ID==ID:
                    food.delete()
                    self.food.remove(food)
        new_food=Food(self.canvas,coordinate,str(ID))
        new_food.show()
        self.food.append(new_food)
    
    def delete_loser(self,loser): #loser: the color(ID) of the loser
        try:
            self.canvas.delete(loser)
        except:
            pass
    
    def win(self):
        print("winnn")
        self.end=True
        self.canvas.delete("all")
        self.canvas.delete(tk.ALL)
        time.sleep(0.5)
        self.canvas.create_rectangle(0,0,500,500,fill="#000000")
        self.canvas.create_text(self.canvas.winfo_width()/2, 
                        self.canvas.winfo_height()/2, 
                        font=('consolas', 70), 
                        text="YOU WIN", fill="red", 
                        tag="gameover")
        
        
# Giving title to the gaming window 
    def run(self,food_info):
        self.window.title("GFG Snake game ") 
        self.score = 0
        self.direction = 'down'
        self.label.pack() 
        self.canvas.pack() 
        self.window.update() 
        window_width = self.window.winfo_width() 
        window_height = self.window.winfo_height() 
        screen_width = self.window.winfo_screenwidth() 
        screen_height = self.window.winfo_screenheight() 

        x = int((screen_width/2) - (window_width/2)) 
        y = int((screen_height/2) - (window_height/2)) 

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}") 

        self.window.bind('<Left>', 
                    lambda event: self.change_direction('left')) 
        self.window.bind('<Right>', 
                    lambda event: self.change_direction('right')) 
        self.window.bind('<Up>', 
                    lambda event: self.change_direction('up')) 
        self.window.bind('<Down>', 
                    lambda event: self.change_direction('down')) 
        
        #initialize self food1 food2
        #food_info: {"food1":[x1,y1],"food2":[x2,y2]}
        self.food1=Food(self.canvas,food_info["food1"],"food1")
        self.food2=Food(self.canvas,food_info["food2"],"food2")
        
        self.food=[self.food1,self.food2]
        for food in self.food:
            food.show()
        
        self.next_turn()

        #detectibg whether the window accidentally closed by the player
        def on_destroy(event):
            if event.widget != self.window:
                self.end=True
        self.window.bind("<Destroy>", on_destroy)
                  
# This code is contributed by genius_general 
if __name__ == "__main__":
    game = Game()
    game.run()

