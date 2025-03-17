# serial_receiver.py

import serial
import time
import threading
from data_parser import parse_line_to_dict
from midi_handler import MidiHandler
import os

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

class SerialReceiver:
    def __init__(self, port="COM4", baud_rate=115200, config_dict=None):
        """
        :param port: Serial port name (e.g. "COM4")
        :param baud_rate: e.g. 115200
        :param config_dict: A shared dictionary from the UI with user-defined mappings,
                            e.g. config_dict["F1"] = "D4", config_dict["AccX"] = "Volume", etc.
        """
        self.config_dict = config_dict if config_dict else {}
        self.running = True
        self.midi_handler = MidiHandler(default_velocity=100)
        
        self.simulate_file = True
        script_dir = os.path.dirname(os.path.realpath(__file__))
        file_name = "fingers.txt"
        self.file_path = os.path.join(script_dir, file_name)
        
        # Keep track of notes currently playing from each F-sensor
        self.current_notes = {}

        # Keep track of the last known volume (for demonstration)
        self.current_volume = 100  # default volume for CC #7

        # Keep track of any "vibrato" or pitch bend values for demonstration
        self.current_bend = 8192  # in standard 0..16383 scale, 8192 is "no bend"

        if not self.simulate_file:
            # ================================================
            # OLD SERIAL CODE - commented out for now
            # ================================================
            try:
                self.ser = serial.Serial(port, baud_rate, timeout=1)
                print(f"Connected to {port} at {baud_rate} baud.")
            except Exception as e:
                print(f"Error opening serial port {port}: {e}")
                raise e

            time.sleep(2)  # Wait for the connection to stabilize
            # Start reading from the serial port in a background thread
            self.thread = threading.Thread(target=self.serial_loop, daemon=True)
            self.thread.start()
        else:
            # ================================================
            # NEW FILE SIMULATION CODE
            # ================================================
            try:
                self.file = open(self.file_path, "r")
                print(f"Simulating input from file: {self.file_path}")
            except Exception as e:
                print(f"Error opening file {self.file_path}: {e}")
                raise e

            self.lines = self.file.readlines()
            if not self.lines:
                print(f"No data found in {self.file_path}!")
                self.lines = []

            self.file.close()
            # Start reading from lines in a background thread
            self.thread = threading.Thread(target=self.file_loop, daemon=True)
            self.thread.start()

    def serial_loop(self):
        """
        Continuously reads lines from the serial port and processes them.
        Expected data format (examples):
            "F1:0,P1:1,AccX:0.4,AccY:-0.2,GyrZ:0.3"
            "F2:1,F3:0,P3:0.8,AccZ:1.2,GyrX:0.1"
        """
        while self.running:
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if line:
                    data_dict = parse_line_to_dict(line)
                    self.process_data(data_dict)
            except Exception as e:
                print("Serial read error:", e)
                
    def file_loop(self):
        index = 0
        while self.running and index < len(self.lines):
            line = self.lines[index].strip()
            if line:
                data_dict = parse_line_to_dict(line)
                print(data_dict)
                self.process_data(data_dict)
            index += 1
            # Add a small delay to simulate "real-time" reading
            time.sleep(0.1)

    def process_data(self, data_dict: dict):
        """
        We ignore P1-P4 entirely in this version and remove any pitch-bend logic from them.
        Instead, we apply pitch bend to the GYR sensors that are marked "Vibrato."
        """

        ############################################################
        # 1) F-sensors => notes (unchanged)
        ############################################################
        for f_sensor in ["F1", "F2", "F3", "F4"]:
            raw_value = data_dict.get(f_sensor, 0)
            chosen_note_name = self.config_dict.get(f_sensor, "None")
            midi_note = note_name_to_midi(chosen_note_name)
            
            is_on = bool(raw_value)  # treat nonzero as ON
            currently_playing = (f_sensor in self.current_notes)

            if is_on and midi_note and not currently_playing:
                self.midi_handler.send_midi_note_on(midi_note)
                self.current_notes[f_sensor] = midi_note
            elif not is_on and currently_playing:
                old_note = self.current_notes[f_sensor]
                self.midi_handler.send_midi_note_off(old_note)
                del self.current_notes[f_sensor]

        ############################################################
        # 2) Accelerometers => Volume (unchanged, additive example)
        ############################################################
        total_acc_volume = 0
        for acc_sensor in ["AccX", "AccY", "AccZ"]:
            if self.config_dict.get(acc_sensor, "None") == "Volume":
                raw_val = data_dict.get(acc_sensor, 0.0)
                abs_val = abs(raw_val)
                # Example: if range is -2..+2
                scaled = int((abs_val / 2.0) * 127)
                scaled = max(0, min(127, scaled))
                total_acc_volume += scaled

        if total_acc_volume > 127:
            total_acc_volume = 127

        if total_acc_volume != self.current_volume:
            self.current_volume = total_acc_volume
            self.midi_handler.send_midi_control_change(7, self.current_volume)

        ############################################################
        # 3) Gyroscopes => pitch bend ("Vibrato") ignoring P-sensors
        #
        # We'll pick the one GYR axis that has the largest magnitude
        # if "Vibrato" is selected in the UI. Then we scale -500..+500
        # into pitch bend range 0..16383, with 8192 as center.
        # The bigger the dead zone, the less small motions matter.
        ############################################################

        # If no GYR sensor is set to "Vibrato," we won't send any pitch bend
        # except to reset it to center once if needed.
        enabled_gyros = []
        for gyr_sensor in ["GyrX", "GyrY", "GyrZ"]:
            if self.config_dict.get(gyr_sensor, "None") == "Vibrato":
                enabled_gyros.append(gyr_sensor)

        # If user didn't enable "Vibrato" on any GYR axis, we can just ensure
        # pitch bend is neutral (8192) if not already, and skip further logic.
        if not enabled_gyros:
            # Only send a "reset pitch bend" if we're not already at 8192
            if self.current_bend != 8192:
                self.current_bend = 8192
                self.midi_handler.send_pitch_bend(8192)
            return  # done

        # Otherwise, at least one axis is set to "Vibrato". 
        # We'll find whichever axis has the largest absolute reading.
        # Then scale that into 0..16383 with a "dead zone."
        # Let's define:
        DEAD_ZONE = 100        # ±100 around zero => no pitch bend
        FULL_SCALE = 500.0     # your ±500 full scale
        CENTER_BEND = 8192
        HALF_RANGE = 8192      # we can bend from 0..16383 => half-range = 8192

        max_deviation = -1
        chosen_val = 0.0
        for gyr_sensor in enabled_gyros:
            raw_val = data_dict.get(gyr_sensor, 0.0)
            # Look at absolute value to find the largest magnitude
            if abs(raw_val) > max_deviation:
                max_deviation = abs(raw_val)
                chosen_val = raw_val

        # chosen_val is the single axis with largest magnitude
        # Convert that to pitch bend with a dead zone
        if abs(chosen_val) < DEAD_ZONE:
            new_bend = CENTER_BEND
        else:
            sign = 1 if chosen_val > 0 else -1
            # Convert the portion beyond the dead zone to 0..1
            portion = (abs(chosen_val) - DEAD_ZONE) / (FULL_SCALE - DEAD_ZONE)
            portion = max(0.0, min(1.0, portion))  # clamp
            offset = int(portion * HALF_RANGE)     # 0..8192
            if sign > 0:
                new_bend = CENTER_BEND + offset
            else:
                new_bend = CENTER_BEND - offset

        # Only send pitch bend if it changed
        if new_bend != self.current_bend:
            self.current_bend = new_bend
            self.midi_handler.send_pitch_bend(self.current_bend)


    def stop(self):
        """
        Cleanly stop reading and close the serial port.
        """
        self.running = False
        try:
            self.ser.close()
        except Exception as e:
            print("Error closing serial port:", e)
            
