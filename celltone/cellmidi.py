# Celltone - Generative music composition using cellular automata
# Copyright (C) 2012   andreas@jansson.me.uk
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 

import math
import time
import threading
import celltone
try:
    import midi
except ImportError:
    celltone.notice('No midi module, midi writing will not work')
try:
    import pypm
except ImportError:
    celltone.notice('No pypm module, midi playing will not work')
            
class Handler(object):

    def __init__(self, bpm, subdivision):
        self.bpm = float(bpm)
        self.thread = None
        self.subdivision = int(subdivision)
        self.time = 0

    def set_tempo(self, tempo):
        self.bpm = float(tempo)

    def set_subdivision(self, subdivision):
        self.subdivision = int(subdivision)

    def play(self, midi_notes):
        self.thread = OutputThread(self, midi_notes)
        self.thread.start()
        return self.thread

    def stop(self):
        leftover_midi_notes = self.thread.midi_notes
        self.thread.midi_notes = []
        return leftover_midi_notes

    def noteon(self, midi_note):
        raise NotImplementedError()

    def noteoff(self, midi_note):
        raise NotImplementedError()

    def after_noteon(self):
        self.time += (60.0 / self.bpm) * ((1.0 / self.subdivision) * 4)

    # TODO: make this a @decorator
    def check_midi_note(self, midi_note):
        if midi_note.pitch < 0 or midi_note.pitch > 127:
            celltone.warning("Bad note number %d" % midi_note.pitch)
            return False
        if midi_note.velocity < 0 or midi_note.velocity > 127:
            celltone.warning("Bad velocity %d" % midi_note.velocity)
            return False
        if midi_note.channel < 0 or midi_note.channel > 15:
            celltone.warning("Bad channel number %d" % midi_note.channel)
            return False
        return True

class Player(Handler):

    def __init__(self, bpm, subdivision):
        Handler.__init__(self, bpm, subdivision)

        pypm.Initialize()
        dev = pypm.GetDefaultOutputDeviceID()
        self.midi_out = pypm.Output(dev)

    def noteon(self, midi_note):
        if self.check_midi_note(midi_note):
            self.midi_out.WriteShort(0x90 + midi_note.channel,
                                     midi_note.pitch, midi_note.velocity)

    def noteoff(self, midi_note):
        if self.check_midi_note(midi_note):
            if midi_note.pitch >= 0 or midi_note.pitch <= 127:
                self.midi_out.WriteShort(0x80 + midi_note.channel,
                                         midi_note.pitch, 0)

    def after_noteon(self):
        Handler.after_noteon(self)
        seconds = (60.0 / self.bpm) * ((1.0 / self.subdivision) * 4)
        time.sleep(seconds)

class Writer(Handler):

    def __init__(self, filename, bpm, subdivision):
        Handler.__init__(self, bpm, subdivision)

        self.filename = filename
        self.track = []
        self.tick = 0
        self.prev_tick = 0
        self.subres = 12

    def noteon(self, note):
        if self.check_midi_note(note):
            on = midi.NoteOnEvent(
                tick = self.delta_tick(), channel = note.channel,
                data = [note.pitch, note.velocity])
            self.track.append(on)

    def noteoff(self, note):
        if self.check_midi_note(note):
            off = midi.NoteOffEvent(
                tick = self.delta_tick(), channel = note.channel,
                data = [note.pitch, note.velocity])
            self.track.append(off)

    def after_noteon(self):
        Handler.after_noteon(self)
        self.tick += self.subres

    def delta_tick(self):
        delta = self.tick - self.prev_tick
        if delta:
            self.prev_tick = self.tick
        return delta

    def make_meta_track(self):
        tempo_event = midi.SetTempoEvent(tick = 0)
        tempo_event.set_bpm(self.bpm)
        eot = midi.EndOfTrackEvent()
        eot.tick = 0
        return [tempo_event, eot]

    def write(self):
        eot = midi.EndOfTrackEvent()
        eot.tick = self.delta_tick()
        self.track.append(eot)
        meta_track = self.make_meta_track()
        pattern = midi.Pattern(tracks = [meta_track, self.track],
                               resolution = math.ceil(self.subres * self.subdivision / 4.0))
        midi.write_midifile(self.filename, pattern)

class OutputThread(threading.Thread):

    def __init__(self, handler, midi_notes):
        self.handler = handler
        self.midi_notes = midi_notes
        threading.Thread.__init__(self)

    def run(self):
        while len(self.midi_notes) > 0:
            notes = self.midi_notes[0]
            self.midi_notes = self.midi_notes[1:]
            for note in notes:
                self.handler.noteon(note)
            self.handler.after_noteon()
            for note in notes:
                self.handler.noteoff(note)

class MidiNote(object):

    def __init__(self, pitch, channel, velocity):
        self.pitch = int(pitch)
        self.channel = int(channel)
        self.velocity = int(velocity)
