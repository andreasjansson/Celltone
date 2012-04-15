from model import MidiNote
import time
import pypm
import threading
import celltone

class Player(threading.Thread):

    try:
        pypm.Initialize()
        dev = pypm.GetDefaultOutputDeviceID()
        midi_out = pypm.Output(dev)
    except Exception as e:
        celltone.die('Failed to start MIDI: ' + str(e))

    def __init__(self, bpm, subdivision):
        self.bpm = float(bpm)
        self.thread = None
        self.subdivision = 1.0 / subdivision

    def play(self, midi_notes):
        self.thread = PlayerThread(self, midi_notes)
        self.thread.start()
        return self.thread

    def stop(self):
        leftover_midi_notes = self.thread.midi_notes
        self.thread.midi_notes = []
        return leftover_midi_notes

    def noteon(self, midi_note):
        if midi_note.note < 0 or midi_note.note > 127:
            celltone.warning("Bad note number %d" % midi_note.note)
        else:
            Player.midi_out.WriteShort(0x90 + midi_note.channel,
                                       midi_note.note, midi_note.velocity)

    def noteoff(self, midi_note):
        if midi_note.note >= 0 or midi_note.note <= 127:
            Player.midi_out.WriteShort(0x80 + midi_note.channel,
                                       midi_note.note, 0)


class PlayerThread(threading.Thread):

    def __init__(self, player, midi_notes):
        self.player = player
        self.midi_notes = midi_notes
        threading.Thread.__init__(self)

    def run(self):
        while len(self.midi_notes) > 0:
            notes = self.midi_notes[0]
            self.midi_notes = self.midi_notes[1:]
            for note in notes:
                self.player.noteon(note)

            seconds = (60.0 / self.player.bpm) * (self.player.subdivision * 4)
            time.sleep(seconds)

            for note in notes:
                self.player.noteoff(note)

