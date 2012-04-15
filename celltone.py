from model import *
from parser import Parser, ParseError
from midi import Player
import sys
import signal
import time

class Celltone:

    def __init__(self, code):
        self.parser = Parser()

        signal.signal(signal.SIGINT, self.exit)

        self.leftover_midi_notes = None
        self.is_playing = False
        self.set_code(code)

        self.play()
        self.loop()

    def exit(self, signal = None, frame = None):
        self.stop()

        # harmless exceptions may be thrown here. surpress
        class Devnull(object):
            def write(self, _): pass
        sys.stderr = Devnull()
        sys.exit(0)

    def set_code(self, code):
        if code:
            try:
                parts, rules, config = self.parser.parse(code)
            except ParseError as e:
                sys.stderr.write(str(e))
                sys.exit(1)
        else:
            parts = []
            rules = []
            config = Config()
            
        self.engine = Engine(parts, rules)
        iterlength = config.get('iterlength')
        if iterlength is not None:
            self.engine.iteration_length = iterlength
        self.player = Player(config.get('tempo'), config.get('subdiv'))

    def loop(self, initial_midi_notes = None):
        '''
        This architecture makes it possible to control Celltone
        from another thread, by calling play(), pause() and stop().
        '''
        while True:
            if self.is_playing:

                if self.leftover_midi_notes:
                    midi_notes = self.leftover_midi_notes
                    self.leftover_midi_notes = None
                else:
                    midi_notes = self.engine.get_midi_notes()

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
    Celltone(code)
