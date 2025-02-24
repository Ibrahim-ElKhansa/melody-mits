# config_ui.py

import tkinter as tk
from tkinter import ttk

# Some example note options. You could expand this or auto-generate from a range.
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

class ConfigUI(tk.Frame):
    """
    A Frame containing dropdowns to configure each sensor’s musical role.
    - F1-F4 => choose a note or "None"
    - P1-P4 => choose "None", "Sharp", or "Flat"
    - AccX,AccY,AccZ => choose "None" or "Volume"
    - GyrX,GyrY,GyrZ => choose "None" or "Vibrato"
    """
    def __init__(self, master, config_dict, *args, **kwargs):
        """
        :param config_dict: A dictionary shared with other modules that stores user selections.
        """
        super().__init__(master, *args, **kwargs)
        self.config_dict = config_dict
        self.init_ui()

    def init_ui(self):
        # We'll have a grid with sections for F, P, Acc, Gyr
        row = 0

        tk.Label(self, text="FLEX SENSORS (F1-F4) => Note").grid(row=row, column=0, columnspan=2, pady=(5,0), sticky="w")
        row += 1
        for sensor in ["F1", "F2", "F3", "F4"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=NOTES, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            # Save references in config_dict
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_flex_change(s, c))
            row += 1

        tk.Label(self, text="PRESSURE SENSORS (P1-P4) => Sharp/Flat").grid(row=row, column=0, columnspan=2, pady=(10,0), sticky="w")
        row += 1
        for sensor in ["P1", "P2", "P3", "P4"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=SHARP_FLAT, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_pressure_change(s, c))
            row += 1

        tk.Label(self, text="ACCELEROMETERS (AccX,AccY,AccZ) => Volume?").grid(row=row, column=0, columnspan=2, pady=(10,0), sticky="w")
        row += 1
        for sensor in ["AccX", "AccY", "AccZ"]:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=VOL_OPTIONS, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_acc_change(s, c))
            row += 1

        tk.Label(self, text="GYROSCOPES (GyrX,GyrY,GyrZ) => Vibrato?").grid(row=row, column=0, columnspan=2, pady=(10,0), sticky="w")
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

def note_name_to_midi(note_name: str):
    """
    Utility function to convert the note name from the UI to a MIDI note number.
    Returns None if note_name is "None" or not found in the map.
    """
    return NOTE_NAME_TO_MIDI.get(note_name, None)
