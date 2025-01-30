import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import socket
import json

class MelodyMitsSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Melody Mits Simulator")
        
        self.finger_states = {"Finger 1": 0, "Finger 2": 0, "Finger 3": 0, "Finger 4": 0}
        self.rotation_angle = 0
        self.position = [200, 200]  # Initial position in the center of 400x400
        
        self.movement = [0, 0]
        self.rotation_movement = 0
        
        self.server_address = ('localhost', 65432)  # Address for data transmission
        self.create_widgets()
        self.setup_plot()
        self.update_movement()
    
    def create_widgets(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack()
        
        self.buttons = {}
        for finger in self.finger_states:
            btn = tk.Button(button_frame, text=finger, command=lambda f=finger: self.toggle_finger(f), width=10, height=2)
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            self.buttons[finger] = btn
        
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        
        self.root.bind("q", lambda event: self.set_finger("Finger 1", 1))
        self.root.bind("w", lambda event: self.set_finger("Finger 2", 1))
        self.root.bind("e", lambda event: self.set_finger("Finger 3", 1))
        self.root.bind("r", lambda event: self.set_finger("Finger 4", 1))
        
        self.root.bind("<KeyRelease-q>", lambda event: self.set_finger("Finger 1", -1))
        self.root.bind("<KeyRelease-w>", lambda event: self.set_finger("Finger 2", -1))
        self.root.bind("<KeyRelease-e>", lambda event: self.set_finger("Finger 3", -1))
        self.root.bind("<KeyRelease-r>", lambda event: self.set_finger("Finger 4", -1))
        
        self.root.bind("<Left>", lambda event: self.start_movement(-10, 0))
        self.root.bind("<Right>", lambda event: self.start_movement(10, 0))
        self.root.bind("<Up>", lambda event: self.start_movement(0, 10))
        self.root.bind("<Down>", lambda event: self.start_movement(0, -10))
        
        self.root.bind("<KeyRelease-Left>", lambda event: self.stop_movement())
        self.root.bind("<KeyRelease-Right>", lambda event: self.stop_movement())
        self.root.bind("<KeyRelease-Up>", lambda event: self.stop_movement())
        self.root.bind("<KeyRelease-Down>", lambda event: self.stop_movement())
        
        self.root.bind("c", lambda event: self.start_rotation(-5))
        self.root.bind("v", lambda event: self.start_rotation(5))
        
        self.root.bind("<KeyRelease-c>", lambda event: self.stop_rotation())
        self.root.bind("<KeyRelease-v>", lambda event: self.stop_rotation())
    
    def setup_plot(self):
        self.ax.clear()
        self.ax.set_xlim(0, 400)
        self.ax.set_ylim(0, 400)
        self.update_plot()
    
    def set_finger(self, finger, value):
        self.finger_states[finger] = value
        self.buttons[finger].config(bg="red" if value == 1 else "SystemButtonFace")
        self.send_data()
    
    def start_movement(self, dx, dy):
        self.movement = [dx, dy]
    
    def stop_movement(self):
        self.movement = [0, 0]
    
    def move(self):
        self.position[0] = max(0, min(400, self.position[0] + self.movement[0]))
        self.position[1] = max(0, min(400, self.position[1] + self.movement[1]))
        self.send_data()
        self.update_plot()
    
    def start_rotation(self, angle):
        self.rotation_movement = angle
    
    def stop_rotation(self):
        self.rotation_movement = 0
    
    def rotate(self):
        self.rotation_angle = (self.rotation_angle + self.rotation_movement) % 360
        self.send_data()
        self.update_plot()
    
    def send_data(self):
        data = json.dumps({"Fingers": self.finger_states, "Position": self.position, "Rotation": self.rotation_angle})
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(data.encode(), self.server_address)
    
    def update_movement(self):
        self.move()
        self.rotate()
        self.root.after(30, self.update_movement)  # Faster refresh rate for smoother motion
    
    def update_plot(self):
        self.ax.clear()
        self.ax.set_xlim(0, 400)
        self.ax.set_ylim(0, 400)
        
        circle = plt.Circle(self.position, 20, color='blue', fill=False)
        arrow_x = self.position[0] + 20 * np.cos(np.radians(self.rotation_angle))
        arrow_y = self.position[1] + 20 * np.sin(np.radians(self.rotation_angle))
        
        self.ax.add_patch(circle)
        self.ax.arrow(self.position[0], self.position[1], arrow_x - self.position[0], arrow_y - self.position[1], 
                      head_width=10, head_length=10, fc='red', ec='red')
        
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
if __name__ == "__main__":
    root = tk.Tk()
    app = MelodyMitsSimulator(root)
    root.mainloop()
