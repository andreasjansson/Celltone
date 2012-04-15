from model import *
from parser import Parser, ParseError
from midi import Player
from gui import Gui, gui_lock
import sys
import signal
import time

class Celltone:

    def __init__(self, code, has_gui):
        self.parser = Parser()

        signal.signal(signal.SIGINT, self.exit)

        if has_gui:
            self.gui = Gui()
            self.gui.on_play = self.play
            self.gui.on_pause = self.pause
            self.gui.on_stop = self.stop
            self.gui.on_compile = self.set_code
            self.gui.on_close = self.exit
        else:
            self.gui = None

        self.leftover_midi_notes = None
        self.is_playing = False

        if has_gui:
            gui_lock.acquire()
            
        self.set_code(code)

        if not self.gui:
            self.play()

        self.loop()

    def exit(self, signal = None, frame = None):
        self.stop()
        if self.gui:
            self.gui.destroy()

        # a harmless exception is always thrown here. let's hide it.
        class Devnull(object):
            def write(self, _): pass
        sys.stderr = Devnull()
        sys.exit(0)

    def set_code(self, code):
        if code:
            try:
                parts, rules, config = self.parser.parse(code)
            except ParseError as e:
                if self.gui:
                    self.gui.show_parse_error(e)
                else:
                    sys.stderr.write(str(e))
                    sys.exit(1)
                pass
        else:
            parts = []
            rules = []
            config = Config()
            
        self.engine = Engine(parts, rules)
        iterlength = config.get('iterlength')
        if iterlength is not None:
            self.engine.iteration_length = iterlength
        self.player = Player(config.get('tempo'), config.get('subdiv'))

        if self.gui:
            self.gui.set_parts(parts)

    def loop(self, initial_midi_notes = None):

        while True:
            if self.is_playing:

                if self.leftover_midi_notes:
                    midi_notes = self.leftover_midi_notes
                    self.leftover_midi_notes = None
                else:
                    midi_notes = self.engine.get_midi_notes()

                if self.gui:
                    self.gui.show_log(logger.items)

                self.player.play(midi_notes)
                logger.clear()
                self.engine.iterate()
        
                # for some reason, this creates a tiny delay,
                # making it unusable. for now, CTRL-C will take
                # some time to kick in.
                # while self.player.thread.is_alive():
                #     self.player.thread.join(1)
                self.player.thread.join()
            else:
                time.sleep(0.5)

    def play(self):
        self.is_playing = True

    def pause(self):
        if not self.is_playing:
            return

        self.is_playing = False
        self.leftover_midi_notes = self.player.stop()

    def stop(self):
        if not self.is_playing:
            return

        self.is_playing = False
        self.player.stop()
        self.engine.reset_parts()

if __name__ == '__main__':
    code = ''.join(sys.stdin.readlines())
    Celltone(code, True)
