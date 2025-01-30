import tkinter as tk
import socket
import json

class MelodyMitsReceiver:
    def __init__(self, root):
        self.root = root
        self.root.title("Melody Mits Receiver")
        
        self.data_label = tk.Label(root, text="Waiting for data...", font=("Arial", 14))
        self.data_label.pack(pady=20)
        
        self.server_address = ('localhost', 65432)
        self.start_receiver()
    
    def start_receiver(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.server_address)
        self.receive_data()
    
    def receive_data(self):
        self.sock.settimeout(0.1)
        try:
            data, _ = self.sock.recvfrom(1024)
            parsed_data = json.loads(data.decode())
            display_text = f"Fingers: {parsed_data['Fingers']}\nPosition: {parsed_data['Position']}\nRotation: {parsed_data['Rotation']}"
            self.data_label.config(text=display_text)
        except socket.timeout:
            pass
        self.root.after(100, self.receive_data)

if __name__ == "__main__":
    root = tk.Tk()
    app = MelodyMitsReceiver(root)
    root.mainloop()
