import tkinter as tk
import threading
import time
import random
from tkinter import ttk

# We'll keep the serial receiver in a separate file for clarity
from serial_receiver import SerialReceiver

#######################################################
# Begin config UI code (originally from config_ui.py) #
#######################################################

# Note definitions for the flex sensor dropdowns
NOTES = [
    "None",
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5"
]

SHARP_FLAT = ["None", "Sharp", "Flat"]
VOL_OPTIONS = ["None", "Volume"]
VIBRATO_OPTIONS = ["None", "Vibrato"]

# A helper to map note names to MIDI note numbers (just partial range).
# In a real application, you'd have a full map of all note names.
NOTE_NAME_TO_MIDI = {
    "None": None,

    "C3": 48,  "C#3": 49,  "D3": 50,  "D#3": 51,  "E3": 52,  "F3": 53,
    "F#3": 54, "G3": 55,   "G#3": 56, "A3": 57,   "A#3": 58, "B3": 59,

    "C4": 60,  "C#4": 61,  "D4": 62,  "D#4": 63,  "E4": 64,  "F4": 65,
    "F#4": 66, "G4": 67,   "G#4": 68, "A4": 69,   "A#4": 70, "B4": 71,

    "C5": 72,  "C#5": 73,  "D5": 74,  "D#5": 75,  "E5": 76,  "F5": 77
}

def note_name_to_midi(note_name: str):
    """
    Utility function to convert the note name from the UI to a MIDI note number.
    Returns None if note_name is "None" or not found in the map.
    """
    return NOTE_NAME_TO_MIDI.get(note_name, None)

class ConfigUI(tk.Frame):
    """
    A Frame containing dropdowns to configure each sensor’s musical role:
     - F1-F4 => choose a note or "None"
     - P1-P4 => choose "None", "Sharp", or "Flat"
     - AccX,AccY,AccZ => choose "None" or "Volume"
     - GyrX,GyrY,GyrZ => choose "None" or "Vibrato"
    """
    def __init__(self, master, config_dict, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config_dict = config_dict
        self.init_ui()

    def init_ui(self):
        row = 0
        # Flex sensors
        tk.Label(self, text="FLEX SENSORS (F1-F4) => Note").grid(
            row=row, column=0, columnspan=2, pady=(5,0), sticky="w"
        )
        row += 1
        for sensor in ["F1", "F2", "F3", "F4"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=NOTES, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_flex_change(s, c))
            row += 1

        # Pressure sensors
        tk.Label(self, text="PRESSURE SENSORS (P1-P4) => Sharp/Flat").grid(
            row=row, column=0, columnspan=2, pady=(10,0), sticky="w"
        )
        row += 1
        for sensor in ["P1", "P2", "P3", "P4"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=SHARP_FLAT, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_pressure_change(s, c))
            row += 1

        # Accelerometers
        tk.Label(self, text="ACCELEROMETERS (AccX,AccY,AccZ) => Volume?").grid(
            row=row, column=0, columnspan=2, pady=(10,0), sticky="w"
        )
        row += 1
        for sensor in ["AccX", "AccY", "AccZ"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=VOL_OPTIONS, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_acc_change(s, c))
            row += 1

        # Gyroscopes
        tk.Label(self, text="GYROSCOPES (GyrX,GyrY,GyrZ) => Vibrato?").grid(
            row=row, column=0, columnspan=2, pady=(10,0), sticky="w"
        )
        row += 1
        for sensor in ["GyrX", "GyrY", "GyrZ"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=VIBRATO_OPTIONS, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_gyro_change(s, c))
            row += 1

    def on_flex_change(self, sensor_name, combo):
        selected = combo.get()
        self.config_dict[sensor_name] = selected

    def on_pressure_change(self, sensor_name, combo):
        selected = combo.get()
        self.config_dict[sensor_name] = selected

    def on_acc_change(self, sensor_name, combo):
        selected = combo.get()
        self.config_dict[sensor_name] = selected

    def on_gyro_change(self, sensor_name, combo):
        selected = combo.get()
        self.config_dict[sensor_name] = selected

###################################################
# End config UI code and begin main application   #
###################################################

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Maker Configuration")

        # Shared config dictionary that the UI writes into and the serial receiver reads from
        self.config_dict = {}

        # Create a frame to hold the config UI
        config_frame = tk.LabelFrame(root, text="Sensor Configuration")
        config_frame.pack(side="left", fill="both", expand=False, padx=5, pady=5)

        # Create the config UI inside config_frame
        self.config_ui = ConfigUI(config_frame, self.config_dict)
        self.config_ui.pack(fill="both", expand=True)

        # Right Frame: Status & Start/Stop Buttons
        right_frame = tk.Frame(root)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        self.start_button = tk.Button(right_frame, text="Start Serial", command=self.start_serial)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(right_frame, text="Stop Serial", command=self.stop_serial, state="disabled")
        self.stop_button.pack(pady=5)

        # Rave Mode Button
        self.rave_mode = False
        self.rave_thread = None
        self.rave_button = tk.Button(right_frame, text="Enable Rave Mode", command=self.toggle_rave_mode)
        self.rave_button.pack(pady=5)

        # A label to display some simple status
        self.status_label = tk.Label(right_frame, text="Serial not running.")
        self.status_label.pack(pady=5)

        # Keep a reference to our SerialReceiver (None until user starts)
        self.serial_receiver = None

        # On close, ensure we stop everything properly
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_serial(self):
        if self.serial_receiver is None:
            self.serial_receiver = SerialReceiver(
                port="COM4",
                baud_rate=115200,
                config_dict=self.config_dict
            )
            self.status_label.config(text="Serial running...")
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")

    def stop_serial(self):
        if self.serial_receiver:
            self.serial_receiver.stop()
            self.serial_receiver = None
            self.status_label.config(text="Serial stopped.")
            self.start_button.config(state="normal")
            self.stop_button.config(state="disabled")

    def toggle_rave_mode(self):
        """
        Toggle rave_mode ON/OFF and update the UI button appearance.
        If turning ON, start a background thread that fires random MIDI events.
        If turning OFF, the thread will see rave_mode=False and exit.
        """
        self.rave_mode = not self.rave_mode
        if self.rave_mode:
            self.rave_button.config(text="Disable Rave Mode", bg="magenta")
            self.start_rave_thread()
        else:
            self.rave_button.config(text="Enable Rave Mode", bg="")
            # Rave thread will see self.rave_mode = False and end gracefully

    def start_rave_thread(self):
        """
        Start a background thread that sends random MIDI events while rave_mode is True.
        If serial isn't running, do nothing.
        """
        if not self.serial_receiver:
            return  # No serial => no MIDI out
        self.rave_thread = threading.Thread(target=self.rave_loop, daemon=True)
        self.rave_thread.start()

    def rave_loop(self):
        """
        Continuously send random MIDI events while rave_mode is True.
        """
        midi = self.serial_receiver.midi_handler
        # Some basic set of notes to pick from (C4, D4, E4, F4, G4, A4)
        note_pool = [60, 62, 64, 65, 67, 69, 71]

        while self.rave_mode:
            note = random.choice(note_pool)
            velocity = random.randint(80, 127)
            # Send note_on
            midi.send_midi_note_on(note, velocity)
            time.sleep(0.1)  # short staccato or tune for desired effect
            # Send note_off
            midi.send_midi_note_off(note)
            time.sleep(0.05)

            # Maybe apply random pitch bends or mod wheel occasionally
            if random.random() < 0.2:  # 20% chance
                # Pitch bend range: 0..16383, with 8192 = no bend
                bend_val = random.randint(0, 16383)
                midi.send_pitch_bend(bend_val)

        # Once rave_mode is turned off, optionally reset pitch bend
        midi.send_pitch_bend(8192)

    def on_closing(self):
        # Ensure that Rave Mode stops, too
        self.rave_mode = False
        if self.rave_thread:
            self.rave_thread.join(timeout=1.0)

        self.stop_serial()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
