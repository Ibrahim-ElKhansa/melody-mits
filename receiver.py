import tkinter as tk
import socket, json, threading, time, math
import mido

class SimulationReceiver:
    def __init__(self, root):
        self.root = root
        self.root.title("Simulation Receiver")
        
        self.info_label = tk.Label(root, text="Waiting for sensor data...", font=("Arial", 12))
        self.info_label.pack(pady=20)
        
        self.server_address = ('localhost', 65432)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.server_address)
        self.sock.settimeout(1.0)
        
        self.running = True
        self.current_note = None  # currently active MIDI note
        self.accel_threshold = 1.0  # threshold to consider the object as moving
        self.volume_factor = 3     # scaling factor for acceleration to velocity
        
        # Map each nonzero finger combination (1..15) to a MIDI note.
        # Bit order: Finger 4 (bit 3), Finger 3 (bit 2), Finger 2 (bit 1), Finger 1 (bit 0)
        self.combination_to_note = {
            1: 60,  2: 62,  3: 64,  4: 65,  5: 67,
            6: 69,  7: 71,  8: 72,  9: 74, 10: 76,
            11: 77, 12: 79, 13: 81, 14: 83, 15: 84
        }
        
        # Parameters for vibrato (pitch bend)
        self.max_rotation = 30  # degrees corresponding to maximum vibrato effect
        self.max_bend = 200     # maximum pitch bend offset (in MIDI pitchbend units, e.g. ±200)
        
        # Initialize MIDI output (adjust port as necessary)
        try:
            self.midi_out = mido.open_output()
        except Exception as e:
            print("MIDI initialization failed:", e)
            self.midi_out = None
        
        threading.Thread(target=self.receive_loop, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def receive_loop(self):
        while self.running:
            try:
                data, _ = self.sock.recvfrom(1024)
                message = json.loads(data.decode())
                self.process_message(message)
            except socket.timeout:
                continue
            except Exception as e:
                print("Receive error:", e)
    
    def process_message(self, message):
        # Retrieve sensor data from the message
        fingers = message.get("Fingers", {})
        acceleration = message.get("Acceleration", [0, 0])
        rotation = message.get("Rotation", 0)
        
        # Compute binary combination: Finger 4 is bit 3 ... Finger 1 is bit 0.
        combination = ((fingers.get("Finger 4", 0) << 3) |
                       (fingers.get("Finger 3", 0) << 2) |
                       (fingers.get("Finger 2", 0) << 1) |
                       fingers.get("Finger 1", 0))
        
        # Calculate acceleration magnitude
        ax, ay = (acceleration if isinstance(acceleration, (list, tuple)) and len(acceleration) >= 2 
                  else (0, 0))
        accel_magnitude = math.sqrt(ax**2 + ay**2)
        
        # Update debugging display
        info_text = f"Combination: {combination}\nAccel: {accel_magnitude:.2f}\nRot: {rotation:.1f}"
        self.root.after(0, self.info_label.config, {"text": info_text})
        
        # If no fingers are active, ensure any active note is turned off
        if combination == 0:
            if self.current_note is not None:
                self.send_midi('note_off', self.current_note, 0)
                self.current_note = None
            return
        
        # Map finger combination to a MIDI note
        note = self.combination_to_note.get(combination, None)
        if note is None:
            return
        
        # Only trigger/update note if sufficient movement is detected
        if accel_magnitude >= self.accel_threshold:
            velocity = min(127, int(accel_magnitude * self.volume_factor))
            if self.current_note != note:
                if self.current_note is not None:
                    self.send_midi('note_off', self.current_note, 0)
                self.send_midi('note_on', note, velocity)
                self.current_note = note
            else:
                # Update volume smoothly using CC 11 (expression)
                self.send_midi_cc(11, velocity)
                # Also update pitch bend based on rotation (vibrato)
                pitch_offset = int((rotation / self.max_rotation) * self.max_bend)
                # Clamp pitch_offset between -max_bend and +max_bend
                pitch_offset = max(-self.max_bend, min(self.max_bend, pitch_offset))
                self.send_pitch_bend(pitch_offset)
        else:
            if self.current_note is not None:
                self.send_midi('note_off', self.current_note, 0)
                self.current_note = None
    
    def send_midi(self, command, note, velocity):
        if self.midi_out:
            try:
                msg = mido.Message(command, note=note, velocity=velocity)
                self.midi_out.send(msg)
            except Exception as e:
                print("MIDI send error:", e)
    
    def send_midi_cc(self, control, value):
        if self.midi_out:
            try:
                msg = mido.Message('control_change', control=control, value=value)
                self.midi_out.send(msg)
            except Exception as e:
                print("MIDI CC send error:", e)
    
    def send_pitch_bend(self, value):
        """Send a pitch bend message. Mido's 'pitchwheel' message expects a signed value."""
        if self.midi_out:
            try:
                # Note: The typical MIDI pitch bend range is -8192 to 8191.
                # Here we send a small offset to simulate vibrato.
                msg = mido.Message('pitchwheel', pitch=value)
                self.midi_out.send(msg)
            except Exception as e:
                print("MIDI pitch bend error:", e)
    
    def on_closing(self):
        self.running = False
        self.sock.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SimulationReceiver(root)
    root.mainloop()
