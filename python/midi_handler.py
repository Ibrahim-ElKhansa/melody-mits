# midi_handler.py

import mido

class MidiHandler:
    def __init__(self, default_velocity=100):
        """
        default_velocity is an integer between 0-127 (standard MIDI velocity range).
        """
        self.default_velocity = default_velocity
        try:
            self.midi_out = mido.open_output()  # Adjust your MIDI port as needed
        except Exception as e:
            print("MIDI initialization failed:", e)
            self.midi_out = None

    def send_midi_note_on(self, note: int, velocity=None):
        """
        Sends a MIDI note_on message. velocity defaults to self.default_velocity if not provided.
        """
        if not self.midi_out:
            return
        if velocity is None:
            velocity = self.default_velocity
        try:
            msg = mido.Message('note_on', note=note, velocity=velocity)
            self.midi_out.send(msg)
        except Exception as e:
            print("MIDI send error (note_on):", e)

    def send_midi_note_off(self, note: int):
        """
        Sends a MIDI note_off message (velocity=0).
        """
        if not self.midi_out:
            return
        try:
            msg = mido.Message('note_off', note=note, velocity=0)
            self.midi_out.send(msg)
        except Exception as e:
            print("MIDI send error (note_off):", e)

    def send_midi_control_change(self, controller: int, value: int):
        """
        Sends a generic MIDI CC (Control Change) message:
            controller is e.g. 1 for Mod Wheel, 7 for Volume, etc.
            value is 0-127
        """
        if not self.midi_out:
            return
        try:
            msg = mido.Message('control_change', control=controller, value=value)
            self.midi_out.send(msg)
        except Exception as e:
            print("MIDI send error (control_change):", e)

    def send_pitch_bend(self, bend_value: int):
        """
        Sends a pitch bend. bend_value is typically in the range -8192 to +8191,
        but mido will do some range adjustment for you if you pass an int 0..16383.
        8192 is neutral (no bend).
        """
        if not self.midi_out:
            return
        try:
            bend_value = max(-8192, min(8191, bend_value))
            msg = mido.Message('pitchwheel', pitch=bend_value)
            self.midi_out.send(msg)
        except Exception as e:
            print("MIDI send error (pitchbend):", e)
