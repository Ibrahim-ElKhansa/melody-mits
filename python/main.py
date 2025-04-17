import tkinter as tk
import threading
import time
from tkinter import ttk
from serial_receiver import SerialReceiver
from midi_handler import MidiHandler

# -------------------------------
# Note and MIDI mappings
# -------------------------------
NOTES = [
    "None",
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5"
]

NOTE_NAME_TO_MIDI = {
    "None": None,
    "C3": 48,  "C#3": 49,  "D3": 50,  "D#3": 51,  "E3": 52,  "F3": 53,
    "F#3": 54, "G3": 55,   "G#3": 56, "A3": 57,   "A#3": 58,  "B3": 59,
    "C4": 60,  "C#4": 61,  "D4": 62,  "D#4": 63,  "E4": 64,  "F4": 65,
    "F#4": 66, "G4": 67,   "G#4": 68, "A4": 69,   "A#4": 70,  "B4": 71,
    "C5": 72,  "C#5": 73,  "D5": 74,  "D#5": 75,  "E5": 76,  "F5": 77
}
# Reverse mapping (for the MIDI numbers we cover)
MIDI_TO_NOTE = {midi: name for name, midi in NOTE_NAME_TO_MIDI.items() if midi is not None}

def note_name_to_midi_func(note_name: str):
    """Utility function to convert a note name to a MIDI number."""
    return NOTE_NAME_TO_MIDI.get(note_name, None)

# -------------------------------
# Scale Computation
# -------------------------------
def compute_scale(root, mode):
    """
    Compute an 8-note diatonic scale based on the given root and mode.
    For Major scale, intervals are: 0, 2, 4, 5, 7, 9, 11, 12 semitones.
    For Minor (natural minor), intervals are: 0, 2, 3, 5, 7, 8, 10, 12.
    The function assumes a default octave 3 for the root.
    Returns a list of note names (if available in our mapping).
    """
    base = root + "3"  # e.g., "C3"
    if base not in NOTE_NAME_TO_MIDI:
        base = root + "3"
    base_midi = NOTE_NAME_TO_MIDI[base]
    if mode == "Major":
        intervals = [0, 2, 4, 5, 7, 9, 11, 12]
    else:  # Minor
        intervals = [0, 2, 3, 5, 7, 8, 10, 12]
    scale_midi = [base_midi + i for i in intervals]
    scale_notes = []
    for midi in scale_midi:
        if midi in MIDI_TO_NOTE:
            scale_notes.append(MIDI_TO_NOTE[midi])
        else:
            # Fallback to numeric representation if not found
            scale_notes.append(str(midi))
    return scale_notes

# -------------------------------
# Config UI (unchanged)
# -------------------------------
CONTROL_NUMBERS = ["None"] + [str(i) for i in range(1, 128)]

class ConfigUI(tk.Frame):
    """
    A frame containing dropdowns to configure each sensor’s musical role:
       - Pressure sensors (P1-P4) => Note name
       - Flex, Accelerometer, and Gyroscope sensors => CC Number
    """
    def __init__(self, master, config_dict, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.config_dict = config_dict
        self.pressure_sensors = ["P1", "P2", "P3", "P4"]
        self.sensor_comboboxes = {}
        self.init_ui()

    def init_ui(self):
        row = 0
        tk.Label(self, text="Pressure Sensors (P1-P4) => Note").grid(
            row=row, column=0, columnspan=2, pady=(5, 0), sticky="w"
        )
        row += 1
        for sensor in self.pressure_sensors:
            tk.Label(self, text=sensor).grid(row=row, column=0, sticky="w", padx=5)
            combo = ttk.Combobox(self, values=NOTES, state="readonly")
            combo.set("None")
            combo.grid(row=row, column=1, padx=5, pady=2, sticky="w")
            self.config_dict[sensor] = "None"
            self.sensor_comboboxes[sensor] = combo
            combo.bind("<<ComboboxSelected>>", lambda e, s=sensor, c=combo: self.on_note_change(s, c))
            row += 1

        # Flex sensors (F1-F4)
        tk.Label(self, text="Flex Sensors (F1-F4) => CC Number").grid(
            row=row, column=0, columnspan=2, pady=(10, 0), sticky="w"
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

        # Accelerometers (AccX, AccY, AccZ)
        tk.Label(self, text="Accelerometers (AccX, AccY, AccZ) => CC Number").grid(
            row=row, column=0, columnspan=2, pady=(10, 0), sticky="w"
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

        # Gyroscopes (GyrX, GyrY, GyrZ)
        tk.Label(self, text="Gyroscopes (GyrX, GyrY, GyrZ) => CC Number").grid(
            row=row, column=0, columnspan=2, pady=(10, 0), sticky="w"
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

    def set_pressure_notes(self, chord_notes):
        """
        Update the four pressure sensor comboboxes with the given list of note names.
        """
        for i, sensor in enumerate(self.pressure_sensors):
            note_name = chord_notes[i]
            self.sensor_comboboxes[sensor].set(note_name)
            self.config_dict[sensor] = note_name

# -------------------------------
# Glove Panel (without chord preset buttons)
# -------------------------------
class GlovePanel(tk.Frame):
    """
    A panel for a single glove: shows sensor configuration and serial control.
    """
    def __init__(self, master, glove_name, port, midi_handler, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.glove_name = glove_name
        self.port = port
        self.config_dict = {}
        self.serial_receiver = None
        self.shared_midi_handler = midi_handler  # store the shared MIDI handler

        # Left: Sensor configuration (using ConfigUI)
        self.config_frame = tk.LabelFrame(self, text=f"{self.glove_name} Sensor Configuration")
        self.config_frame.pack(fill="both", expand=True, padx=5, pady=5)
        self.config_ui = ConfigUI(self.config_frame, self.config_dict)
        self.config_ui.pack(fill="both", expand=True)

        # Right: Control buttons (Start/Stop & status)
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.start_button = tk.Button(self.control_frame, text="Start Serial", command=self.start_serial)
        self.start_button.pack(pady=5)
        self.stop_button = tk.Button(self.control_frame, text="Stop Serial", command=self.stop_serial, state="disabled")
        self.stop_button.pack(pady=5)
        self.status_label = tk.Label(self.control_frame, text="Serial not running.")
        self.status_label.pack(pady=5)

    def start_serial(self):
        if self.serial_receiver is None:
            self.serial_receiver = SerialReceiver(
                port=self.port, 
                baud_rate=115200,
                config_dict=self.config_dict, 
                glove_name=self.glove_name, 
                midi_handler=self.shared_midi_handler  # pass the shared instance
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

    def on_close(self):
        self.stop_serial()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Maker Configuration")

        # Create a single shared MidiHandler.
        self.shared_midi_handler = MidiHandler(default_velocity=100)

        # Global Scale Selection Panel at the top
        self.scale_frame = tk.LabelFrame(root, text="Scale Selection")
        self.scale_frame.pack(fill="x", padx=5, pady=5)

        self.selected_root = tk.StringVar(value="C")
        self.selected_mode = tk.StringVar(value="Major")

        root_label = tk.Label(self.scale_frame, text="Root Note:")
        root_label.pack(side="left", padx=5)
        for note in ["A", "B", "C", "D", "E", "F", "G"]:
            btn = tk.Radiobutton(self.scale_frame, text=note, variable=self.selected_root, value=note, command=self.update_scale)
            btn.pack(side="left", padx=2)

        mode_label = tk.Label(self.scale_frame, text="Mode:")
        mode_label.pack(side="left", padx=10)
        for mode in ["Major", "Minor"]:
            btn = tk.Radiobutton(self.scale_frame, text=mode, variable=self.selected_mode, value=mode, command=self.update_scale)
            btn.pack(side="left", padx=2)

        self.glove_container = tk.Frame(root)
        self.glove_container.pack(fill="both", expand=True, padx=5, pady=5)

        self.glove1_panel = GlovePanel(self.glove_container, glove_name="Glove 1", port="COM5", midi_handler=self.shared_midi_handler)
        self.glove1_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.glove2_panel = GlovePanel(self.glove_container, glove_name="Glove 2", port="COM4", midi_handler=self.shared_midi_handler)
        self.glove2_panel.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.update_scale()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_scale(self):
        scale = compute_scale(self.selected_root.get(), self.selected_mode.get())
        if len(scale) >= 8:
            self.glove1_panel.config_ui.set_pressure_notes(scale[0:4])
            self.glove2_panel.config_ui.set_pressure_notes(scale[4:8])
        print("Updated scale:", scale)

    def on_closing(self):
        self.glove1_panel.on_close()
        self.glove2_panel.on_close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
