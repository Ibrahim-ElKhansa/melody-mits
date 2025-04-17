# serial_receiver.py
import serial
import time
import threading
from data_parser import parse_line_to_dict
from midi_handler import MidiHandler
import os

# Mapping for note names used by pressure sensors (P1-P4)
NOTE_NAME_TO_MIDI = {
    "None": None,
    "C3": 48,  "C#3": 49,  "D3": 50,  "D#3": 51,  "E3": 52,  "F3": 53,
    "F#3": 54, "G3": 55,   "G#3": 56, "A3": 57,   "A#3": 58,  "B3": 59,
    "C4": 60,  "C#4": 61,  "D4": 62,  "D#4": 63,  "E4": 64,  "F4": 65,
    "F#4": 66, "G4": 67,   "G#4": 68, "A4": 69,   "A#4": 70,  "B4": 71,
    "C5": 72,  "C#5": 73,  "D5": 74,  "D#5": 75,  "E5": 76,  "F5": 77
}

def note_name_to_midi(note_name: str):
    return NOTE_NAME_TO_MIDI.get(note_name, None)

class SerialReceiver:
    def __init__(self, port="COM4", baud_rate=115200, config_dict=None, glove_name="Glove 1", midi_handler=None):
        """
        :param port: Serial port (e.g., "COM4")
        :param baud_rate: baud rate (e.g., 115200)
        :param config_dict: Shared sensor configuration dictionary.
        :param glove_name: Identifier for the glove (used in logging).
        :param midi_handler: Shared MidiHandler instance; if None, a new one is created.
        """
        self.glove_name = glove_name
        self.config_dict = config_dict if config_dict else {}
        self.running = True
        
        # Use the shared MidiHandler if provided.
        if midi_handler is not None:
            self.midi_handler = midi_handler
        else:
            self.midi_handler = MidiHandler(default_velocity=100)
        
        self.simulate_file = False
        script_dir = os.path.dirname(os.path.realpath(__file__))
        file_name = "fingers.txt"
        self.file_path = os.path.join(script_dir, file_name)
        
        self.current_notes = {}

        if not self.simulate_file:
            try:
                self.ser = serial.Serial(port, baud_rate, timeout=1)
                print(f"[{self.glove_name}] Connected to {port} at {baud_rate} baud.")
            except Exception as e:
                print(f"[{self.glove_name}] Error opening serial port {port}: {e}")
                raise e

            time.sleep(2)
            self.thread = threading.Thread(target=self.serial_loop, daemon=True)
            self.thread.start()
        else:
            try:
                self.file = open(self.file_path, "r")
                print(f"[{self.glove_name}] Simulating input from file: {self.file_path}")
            except Exception as e:
                print(f"[{self.glove_name}] Error opening file {self.file_path}: {e}")
                raise e

            self.lines = self.file.readlines()
            if not self.lines:
                print(f"[{self.glove_name}] No data found in {self.file_path}!")
                self.lines = []
            self.file.close()
            self.thread = threading.Thread(target=self.file_loop, daemon=True)
            self.thread.start()

    def serial_loop(self):
        while self.running:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                print(f"[{self.glove_name}] {line}")
                if line:
                    data_dict = parse_line_to_dict(line)
                    self.process_data(data_dict)
            except Exception as e:
                print(f"[{self.glove_name}] Serial read error: {e}")
                
    def file_loop(self):
        index = 0
        while self.running and index < len(self.lines):
            line = self.lines[index].strip()
            if line:
                data_dict = parse_line_to_dict(line)
                print(f"[{self.glove_name} File] {data_dict}")
                self.process_data(data_dict)
            index += 1
            time.sleep(0.1)

    def process_data(self, data_dict: dict):
        # Process pressure sensors (P1-P4)
        for sensor in ["P1", "P2", "P3", "P4"]:
            raw_value = data_dict.get(sensor, 0)
            chosen_note_name = self.config_dict.get(sensor, "None")
            midi_note = note_name_to_midi(chosen_note_name)
            is_on = bool(raw_value)
            currently_playing = sensor in self.current_notes
            
            if is_on and midi_note and not currently_playing:
                self.midi_handler.send_midi_note_on(midi_note)
                self.current_notes[sensor] = midi_note
            elif not is_on and currently_playing:
                old_note = self.current_notes[sensor]
                self.midi_handler.send_midi_note_off(old_note)
                del self.current_notes[sensor]
        
        # Process other sensors as continuous controllers (CC)
        sensors_cc = ["F1", "F2", "F3", "F4", "AccX", "AccY", "AccZ", "GyrX", "GyrY", "GyrZ"]
        for sensor in sensors_cc:
            cc_config = self.config_dict.get(sensor, "None")
            if cc_config == "None":
                continue
            try:
                cc_number = int(cc_config)
            except ValueError:
                continue
            raw_val = data_dict.get(sensor, 0.0)
            if sensor.startswith("F"):
                R = 2.0
            elif sensor.startswith("Acc"):
                R = 2.0
            elif sensor.startswith("Gyr"):
                R = 500.0
            else:
                R = 1.0
            mapped_val = int(((raw_val + R) / (2 * R)) * 127)
            mapped_val = max(0, min(127, mapped_val))
            self.midi_handler.send_midi_control_change(controller=cc_number, value=mapped_val)

    def stop(self):
        self.running = False
        try:
            self.ser.close()
        except Exception as e:
            print(f"[{self.glove_name}] Error closing serial port:", e)
