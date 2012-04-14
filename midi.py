from model import MidiNote
import time
import pypm

class Player:

    def __init__(self, bpm, subdivision = 8):
        self.bpm = float(bpm)
        self.subdivision = 1.0 / subdivision

        pypm.Initialize()
        dev = pypm.GetDefaultOutputDeviceID()
        self.midi_out = pypm.Output(dev)

    def play(self, midi_notes):
        for t, notes in midi_notes.iteritems():
            for note in notes:
                self.noteon(note)
            self.sleep()
            for note in notes:
                self.noteoff(note)

    def noteon(self, midi_note):
        self.midi_out.WriteShort(0x90 + midi_note.channel,
                                 midi_note.note, midi_note.velocity)

    def noteoff(self, midi_note):
        self.midi_out.WriteShort(0x80 + midi_note.channel,
                                 midi_note.note, 0)

    def sleep(self):
        seconds = (60.0 / self.bpm) * (self.subdivision * 4)
        time.sleep(seconds)
