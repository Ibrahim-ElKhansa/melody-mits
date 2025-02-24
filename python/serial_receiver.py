# serial_receiver.py

import serial
import time
import threading
from data_parser import parse_line_to_dict
from midi_handler import MidiHandler

from config_ui import note_name_to_midi

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

        # Keep track of notes currently playing from each F-sensor
        self.current_notes = {}

        # Keep track of the last known volume (for demonstration)
        self.current_volume = 100  # default volume for CC #7

        # Keep track of any "vibrato" or pitch bend values for demonstration
        self.current_bend = 8192  # in standard 0..16383 scale, 8192 is "no bend"

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

    def process_data(self, data_dict: dict):
        """
        Interpret the raw data_dict according to self.config_dict, then trigger MIDI events.
        data_dict might look like:
            {
              "F1": 1,
              "F2": 0,
              "P1": 0.2,
              "AccX": 0.7,
              "GyrZ": -0.4
            }
        """

        # 1) Handle the F-sensors (F1-F4) to produce notes.
        for f_sensor in ["F1", "F2", "F3", "F4"]:
            raw_value = data_dict.get(f_sensor, 0)
            # The user has chosen e.g. "D4" or "None"
            chosen_note_name = self.config_dict.get(f_sensor, "None")
            midi_note = note_name_to_midi(chosen_note_name)
            
            is_on = bool(raw_value)  # if > 0, treat it as ON
            currently_playing = f_sensor in self.current_notes

            # If sensor is ON & not playing => note_on
            if is_on and midi_note and not currently_playing:
                self.midi_handler.send_midi_note_on(midi_note)
                self.current_notes[f_sensor] = midi_note

            # If sensor is OFF but it was playing => note_off
            elif not is_on and currently_playing:
                old_note = self.current_notes[f_sensor]
                self.midi_handler.send_midi_note_off(old_note)
                del self.current_notes[f_sensor]

        # 2) Handle the P-sensors (P1-P4) => Sharp/Flat
        #    For demonstration, let's say "Sharp" = +1 semitone, "Flat" = -1 semitone.
        #    We'll shift notes that are currently playing. (In a real scenario, you might store
        #    separate shift for each F-sensor, etc.)
        pitch_shift = 0
        for p_sensor in ["P1", "P2", "P3", "P4"]:
            raw_val = data_dict.get(p_sensor, 0)
            press_option = self.config_dict.get(p_sensor, "None")
            if press_option == "Sharp" and raw_val > 0:
                pitch_shift = 1  # if any P-sensor is pressed "Sharp", we shift by +1
            elif press_option == "Flat" and raw_val > 0:
                pitch_shift = -1
            # If multiple sensors are pressed, you could define a more sophisticated logic.

        # For simplicity, we apply pitch bend as semitone shift.
        # One semitone in pitch bend = about ±4096 offset from 8192. Let's do:
        if pitch_shift == 1:
            # shift up one semitone
            self.current_bend = 8192 + 4096
        elif pitch_shift == -1:
            # shift down one semitone
            self.current_bend = 8192 - 4096
        else:
            self.current_bend = 8192

        self.midi_handler.send_pitch_bend(self.current_bend)

        # 3) Handle accelerometers (AccX,AccY,AccZ) => Volume
        #    If the config says "Volume" for e.g. AccX, we read the raw_value from data_dict, scale it, and send CC #7.
        new_volume = self.current_volume
        for acc_sensor in ["AccX", "AccY", "AccZ"]:
            raw_val = data_dict.get(acc_sensor, 0.0)
            if self.config_dict.get(acc_sensor, "None") == "Volume":
                # example: scale raw_val (which might be from -1..+1 or 0..1.0) to 0..127
                # You decide the appropriate scaling logic.
                scaled = int((raw_val + 1.0) * 63.5)  # if raw_val is -1..+1 => 0..127
                scaled = max(0, min(127, scaled))    # clamp
                new_volume = scaled

        if new_volume != self.current_volume:
            self.current_volume = new_volume
            self.midi_handler.send_midi_control_change(7, self.current_volume)  # CC #7 = main volume

        # 4) Handle gyroscopes (GyrX,GyrY,GyrZ) => Vibrato
        #    For demonstration, let's say "Vibrato" => we send CC #1 (mod wheel) from 0..127.
        vibrato_value = 0
        for gyr_sensor in ["GyrX", "GyrY", "GyrZ"]:
            raw_val = data_dict.get(gyr_sensor, 0.0)
            if self.config_dict.get(gyr_sensor, "None") == "Vibrato":
                # Example: scale raw_val to 0..127. 
                # Again, your real logic depends on your sensor range
                vib = int((raw_val + 1.0) * 63.5)
                vib = max(0, min(127, vib))
                # Just pick the largest from any Gyr sensor that says "Vibrato"
                vibrato_value = max(vibrato_value, vib)

        # Send mod wheel message
        self.midi_handler.send_midi_control_change(1, vibrato_value)

    def stop(self):
        """
        Cleanly stop reading and close the serial port.
        """
        self.running = False
        try:
            self.ser.close()
        except Exception as e:
            print("Error closing serial port:", e)
