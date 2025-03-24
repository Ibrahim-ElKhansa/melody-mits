import tkinter as tk
import threading
import time
import random
from tkinter import ttk

# We'll keep the serial receiver in a separate file for clarity
from serial_receiver import SerialReceiver

#######################################################
# Begin config UI code (modified per your instructions)
#######################################################

# Note definitions for the pressure sensor dropdowns
NOTES = [
    "None",
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5"
]

# Map note names to MIDI numbers, partial range as example
NOTE_NAME_TO_MIDI = {
    "None": None,
    "C3": 48,  "C#3": 49,  "D3": 50,  "D#3": 51,  "E3": 52,  "F3": 53,
    "F#3": 54, "G3": 55,   "G#3": 56, "A3": 57,   "A#3": 58,  "B3": 59,

    "C4": 60,  "C#4": 61,  "D4": 62,  "D#4": 63,  "E4": 64,  "F4": 65,
    "F#4": 66, "G4": 67,   "G#4": 68, "A4": 69,   "A#4": 70,  "B4": 71,

    "C5": 72,  "C#5": 73,  "D5": 74,  "D#5": 75,  "E5": 76,  "F5": 77
}

def note_name_to_midi(note_name: str):
    """ Utility function to convert UI note name to a MIDI note number. """
    return NOTE_NAME_TO_MIDI.get(note_name, None)

# Generate a list of CC numbers [None, 1, 2, ..., 127].
CONTROL_NUMBERS = ["None"] + [str(i) for i in range(1, 128)]

class ConfigUI(tk.Frame):
    """
    A Frame containing dropdowns to configure each sensor’s musical role:
       - P1-P4 => Note name (or None)
       - F1-F4, AccX, AccY, AccZ, GyrX, GyrY, GyrZ => CC number (or None)
    """
    def __init__(self, master, config_dict, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config_dict = config_dict
        self.init_ui()

    def init_ui(self):
        row = 0

        # PRESSURE SENSORS => Note
        tk.Label(self, text="Pressure Sensors (P1-P4) => Note").grid(
            row=row, column=0, columnspan=2, pady=(5,0), sticky="w"
        )
        row += 1
        for sensor in ["P1", "P2", "P3", "P4"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=NOTES, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_note_change(s, c))
            row += 1

        # FLEX SENSORS => CC
        tk.Label(self, text="Flex Sensors (F1-F4) => CC Number").grid(
            row=row, column=0, columnspan=2, pady=(10,0), sticky="w"
        )
        row += 1
        for sensor in ["F1", "F2", "F3", "F4"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=CONTROL_NUMBERS, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_cc_change(s, c))
            row += 1

        # ACCELEROMETERS => CC
        tk.Label(self, text="Accelerometers (AccX, AccY, AccZ) => CC Number").grid(
            row=row, column=0, columnspan=2, pady=(10,0), sticky="w"
        )
        row += 1
        for sensor in ["AccX", "AccY", "AccZ"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=CONTROL_NUMBERS, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_cc_change(s, c))
            row += 1

        # GYROSCOPES => CC
        tk.Label(self, text="Gyroscopes (GyrX, GyrY, GyrZ) => CC Number").grid(
            row=row, column=0, columnspan=2, pady=(10,0), sticky="w"
        )
        row += 1
        for sensor in ["GyrX", "GyrY", "GyrZ"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=CONTROL_NUMBERS, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_cc_change(s, c))
            row += 1

    def on_note_change(self, sensor_name, combo):
        selected = combo.get()
        self.config_dict[sensor_name] = selected

    def on_cc_change(self, sensor_name, combo):
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

    def on_closing(self):
        self.stop_serial()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
