import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import socket, json, threading, time, queue

class SimulationSender:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulation Sender")
        
        # Simulation state: finger states, position, rotation, acceleration
        self.finger_states = {"Finger 1": 0, "Finger 2": 0, "Finger 3": 0, "Finger 4": 0}
        self.rotation_angle = 0.0  # now a signed value (in degrees) used for vibrato
        self.rotation_movement = 0  # incremental change from key presses
        self.position = [200, 200]
        self.movement = [0, 0]
        self.acceleration = (0, 0)
        
        self.server_address = ('localhost', 65432)
        
        # Queue for sending messages immediately (no random delay)
        self.send_queue = queue.Queue()
        self.running = True
        threading.Thread(target=self.process_send_queue, daemon=True).start()
        
        self.create_widgets()
        self.setup_plot()
        
        # Variables for mouse dragging (for position and acceleration)
        self.mouse_dragging = False
        self.last_mouse_pos = (None, None)
        self.last_mouse_time = None
        self.velocity = (0, 0)
        
        self.update_loop()
    
    def create_widgets(self):
        # Create buttons for each finger (these set which note will be produced)
        button_frame = tk.Frame(self.root)
        button_frame.pack()
        self.buttons = {}
        for finger in self.finger_states:
            btn = tk.Button(button_frame, text=finger, command=lambda f=finger: self.toggle_finger(f),
                            width=10, height=2)
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            self.buttons[finger] = btn
        
        # Set up a matplotlib figure embedded in Tkinter for visualization
        self.fig, self.ax = plt.subplots(figsize=(4, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack()
        
        # Bind keys for finger toggling
        self.root.bind("q", lambda event: self.set_finger("Finger 1", 1))
        self.root.bind("w", lambda event: self.set_finger("Finger 2", 1))
        self.root.bind("e", lambda event: self.set_finger("Finger 3", 1))
        self.root.bind("r", lambda event: self.set_finger("Finger 4", 1))
        self.root.bind("<KeyRelease-q>", lambda event: self.set_finger("Finger 1", 0))
        self.root.bind("<KeyRelease-w>", lambda event: self.set_finger("Finger 2", 0))
        self.root.bind("<KeyRelease-e>", lambda event: self.set_finger("Finger 3", 0))
        self.root.bind("<KeyRelease-r>", lambda event: self.set_finger("Finger 4", 0))
        
        # Bind keys for rotation (vibrato control)
        self.root.bind("c", lambda event: self.start_rotation(-5))
        self.root.bind("v", lambda event: self.start_rotation(5))
        self.root.bind("<KeyRelease-c>", lambda event: self.stop_rotation())
        self.root.bind("<KeyRelease-v>", lambda event: self.stop_rotation())
        
        # Instead of Tkinter mouse events, use Matplotlib's mpl_connect so we have xdata/ydata.
        self.canvas.mpl_connect("button_press_event", self.on_mouse_press)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_drag)
        self.canvas.mpl_connect("button_release_event", self.on_mouse_release)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_plot(self):
        self.ax.clear()
        self.ax.set_xlim(0, 400)
        self.ax.set_ylim(0, 400)
        self.update_plot()
    
    def toggle_finger(self, finger):
        new_state = 0 if self.finger_states[finger] == 1 else 1
        self.set_finger(finger, new_state)
    
    def set_finger(self, finger, value):
        self.finger_states[finger] = value
        self.buttons[finger].config(bg="red" if value == 1 else "SystemButtonFace")
        self.send_data()
    
    def start_rotation(self, angle_change):
        self.rotation_movement = angle_change
    
    def stop_rotation(self):
        self.rotation_movement = 0
    
    def rotate(self):
        # Update rotation if a key is pressed; otherwise, decay toward 0
        if self.rotation_movement != 0:
            self.rotation_angle += self.rotation_movement
        else:
            self.rotation_angle *= 0.9  # damping: gradual return toward 0
    
    def move(self):
        # Update position via keyboard if not dragging (here left for possible extension)
        if not self.mouse_dragging:
            self.position[0] = max(0, min(400, self.position[0] + self.movement[0]))
            self.position[1] = max(0, min(400, self.position[1] + self.movement[1]))
    
    def send_data(self):
        # Package sensor data into a JSON message
        data = {
            "Fingers": self.finger_states,
            "Position": self.position,
            "Rotation": self.rotation_angle,
            "Acceleration": self.acceleration
        }
        json_data = json.dumps(data)
        print("Sending data:", json_data)  # Debug output
        self.send_queue.put(json_data)
    
    def process_send_queue(self):
        while self.running:
            try:
                message = self.send_queue.get(timeout=0.1)
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.sendto(message.encode(), self.server_address)
            except queue.Empty:
                continue
    
    def update_loop(self):
        if not self.running:
            return
        self.move()
        self.rotate()
        self.send_data()
        self.update_plot()
        self.root.after(30, self.update_loop)
    
    def update_plot(self):
        self.ax.clear()
        self.ax.set_xlim(0, 400)
        self.ax.set_ylim(0, 400)
        circle = plt.Circle(self.position, 20, color='blue', fill=False)
        arrow_x = self.position[0] + 20 * np.cos(np.radians(self.rotation_angle))
        arrow_y = self.position[1] + 20 * np.sin(np.radians(self.rotation_angle))
        self.ax.add_patch(circle)
        self.ax.arrow(self.position[0], self.position[1],
                      arrow_x - self.position[0], arrow_y - self.position[1],
                      head_width=10, head_length=10, fc='red', ec='red')
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.canvas.draw()
    
    # Mouse event handlers using Matplotlib events
    def on_mouse_press(self, event):
        if event.xdata is not None and event.ydata is not None:
            self.mouse_dragging = True
            self.last_mouse_time = time.time()
            self.last_mouse_pos = (event.xdata, event.ydata)
    
    def on_mouse_drag(self, event):
        if event.xdata is not None and event.ydata is not None and self.mouse_dragging:
            current_time = time.time()
            current_pos = (event.xdata, event.ydata)
            dt = current_time - self.last_mouse_time if self.last_mouse_time else 0.01
            if dt < 1e-6:
                dt = 1e-6
            dx = current_pos[0] - self.last_mouse_pos[0]
            dy = current_pos[1] - self.last_mouse_pos[1]
            current_velocity = (dx / dt, dy / dt)
            if self.velocity != (0, 0):
                ax_val = (current_velocity[0] - self.velocity[0]) / dt
                ay_val = (current_velocity[1] - self.velocity[1]) / dt
                self.acceleration = (ax_val, ay_val)
            else:
                self.acceleration = (0, 0)
            self.velocity = current_velocity
            self.last_mouse_time = current_time
            self.last_mouse_pos = current_pos
            self.position = [current_pos[0], current_pos[1]]
            self.send_data()
    
    def on_mouse_release(self, event):
        self.mouse_dragging = False
        self.acceleration = (0, 0)
        self.send_data()
    
    def on_closing(self):
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationSender(root)
    root.mainloop()
