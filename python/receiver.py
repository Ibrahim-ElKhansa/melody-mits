import serial
import time
import tkinter as tk
import threading
import mido

class SerialReceiver:
    def __init__(self, root, bluetooth_port="COM4", baud_rate=115200):
        self.root = root
        self.root.title("Serial Receiver - Music Maker")
        
        self.info_label = tk.Label(root, text="Waiting for sensor data...", font=("Arial", 12))
        self.info_label.pack(pady=20)
        
        # Initialize the serial port.
        try:
            self.ser = serial.Serial(bluetooth_port, baud_rate, timeout=1)
            print(f"Connected to {bluetooth_port} at {baud_rate} baud.")
        except Exception as e:
            print(f"Error opening serial port: {e}")
            exit(1)
        
        time.sleep(2)  # Allow time for the connection to stabilize
        
        self.running = True
        
        # Increased default velocity for louder sound.
        self.default_velocity = 100  # Adjust between 0 and 127 as needed
        
        # Map each finger (sensor) to a separate MIDI note.
        # Adjust the note numbers as desired.
        self.finger_to_note = {
            "Finger 1": 62,  # C4
            "Finger 2": 60,  # D4
            "Finger 3": 65,  # E4
            "Finger 4": 64   # F4
        }
        
        # Keep track of currently active notes for each finger.
        self.current_notes = {}  # e.g., {"Finger 1": True, ...}
        
        # Initialize MIDI output (adjust port as needed).
        try:
            self.midi_out = mido.open_output()
        except Exception as e:
            print("MIDI initialization failed:", e)
            self.midi_out = None
        
        # Start a background thread to read from the serial port.
        threading.Thread(target=self.serial_receive_loop, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def serial_receive_loop(self):
        while self.running:
            try:
                # Read one line from the serial port.
                line = self.ser.readline().decode('utf-8').rstrip()
                if line:
                    print("Received:", line)
                    # Parse the line. Expected format: 
                    # "Sensor1:OFF,Sensor2:OFF,Sensor3:OFF,Sensor4:OFF"
                    sensors = line.split(',')
                    fingers = {}
                    for sensor in sensors:
                        parts = sensor.split(':')
                        if len(parts) == 2:
                            sensor_name = parts[0].strip()
                            state_str = parts[1].strip()
                            # Map "SensorX" to "Finger X"
                            if sensor_name.startswith("Sensor"):
                                finger_num = sensor_name.replace("Sensor", "")
                                finger_key = f"Finger {finger_num}"
                                fingers[finger_key] = 1 if state_str.upper() == "ON" else 0
                    # Build a message similar to the previous format.
                    message = {
                        "Fingers": fingers
                    }
                    self.process_message(message)
            except Exception as e:
                print("Serial read error:", e)
    
    def process_message(self, message):
        # Retrieve sensor (finger) data.
        fingers = message.get("Fingers", {})
        
        # Update the GUI display with the current status of each finger.
        status_lines = []
        for finger in self.finger_to_note:
            state = "ON" if fingers.get(finger, 0) == 1 else "OFF"
            status_lines.append(f"{finger}: {state}")
        info_text = "\n".join(status_lines)
        self.root.after(0, self.info_label.config, {"text": info_text})
        
        # For each finger, send MIDI note messages based on its state.
        for finger, note in self.finger_to_note.items():
            state = fingers.get(finger, 0)
            if state == 1 and finger not in self.current_notes:
                # If the finger sensor is ON and note is not already active, trigger note on.
                self.send_midi('note_on', note, self.default_velocity)
                self.current_notes[finger] = True
            elif state == 0 and finger in self.current_notes:
                # If the sensor is OFF and note was active, trigger note off.
                self.send_midi('note_off', note, 0)
                del self.current_notes[finger]
    
    def send_midi(self, command, note, velocity):
        if self.midi_out:
            try:
                msg = mido.Message(command, note=note, velocity=velocity)
                self.midi_out.send(msg)
            except Exception as e:
                print("MIDI send error:", e)
    
    def on_closing(self):
        self.running = False
        try:
            self.ser.close()
        except Exception as e:
            print("Error closing serial port:", e)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # Update the port and baud rate as needed.
    app = SerialReceiver(root, bluetooth_port="COM4", baud_rate=115200)
    root.mainloop()
