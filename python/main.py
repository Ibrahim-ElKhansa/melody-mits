# main.py

import tkinter as tk
import threading
import time
import random

from config_ui import ConfigUI
from serial_receiver import SerialReceiver


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

        # On close
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
