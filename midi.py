from model import MidiNote
import time
import pypm
import threading

class Player(threading.Thread):

    pypm.Initialize()
    dev = pypm.GetDefaultOutputDeviceID()
    midi_out = pypm.Output(dev)

    def __init__(self, bpm, subdivision):
        self.bpm = float(bpm)
        self.subdivision = 1.0 / subdivision

    def play(self, midi_notes):
        self.thread = PlayerThread(self, midi_notes)
        self.thread.start()
        return self.thread

    def noteon(self, midi_note):
        Player.midi_out.WriteShort(0x90 + midi_note.channel,
                                 midi_note.note, midi_note.velocity)

    def noteoff(self, midi_note):
        Player.midi_out.WriteShort(0x80 + midi_note.channel,
                                 midi_note.note, 0)


class PlayerThread(threading.Thread):

    def __init__(self, player, midi_notes):
        self.player = player
        self.midi_notes = midi_notes
        threading.Thread.__init__(self)

    def run(self):
        for t, notes in self.midi_notes.iteritems():
            for note in notes:
                self.player.noteon(note)

            seconds = (60.0 / self.player.bpm) * (self.player.subdivision * 4)
            time.sleep(seconds)

            for note in notes:
                self.player.noteoff(note)
