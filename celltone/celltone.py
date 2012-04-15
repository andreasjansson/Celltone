from model import Engine, logger
from parser import Parser, ParseError
from midi import Player
import sys
import signal
import time
import os
import os.path

celltone_home = os.path.expanduser('~/.celltone')

class Celltone:

    def __init__(self, code, verbosity = 0):
        if not os.path.exists(celltone_home):
            os.mkdir(celltone_home)

        self.parser = Parser()
        if verbosity > 0:
            from verbose import Verbose
            self.verbose = Verbose(verbosity)
        else:
            self.verbose = None

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
                die(str(e))

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

                if self.verbose:
                    self.verbose.print_log(logger.items)
                    self.verbose.print_parts(self.engine.parts)

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


def main():
    import argparse
    parser = argparse.ArgumentParser(description = 'Process Celltone code')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', action = 'store_true', help = 'verbose')
    group.add_argument('-vv', action = 'store_true', help = 'more verbose')
    group.add_argument('-vvv', action = 'store_true', help = 'even more verbose')
    parser.add_argument('filename', nargs = '?', help = 'if omitted reads from stdin')
    args = parser.parse_args()

    verbosity = 0
    if args.v:
        verbosity = 1
    if args.vv:
        verbosity = 2
    if args.vvv:
        verbosity = 3

    if not args.filename or args.filename == '-':
        code = ''.join(sys.stdin.readlines())
    else:
        if not os.path.exists(args.filename):
            die('No such file: ' + args.filename)
        with open(args.filename) as f:
            code = ''.join(f.readlines())

    Celltone(code, verbosity)

def die(string, return_code = 1):
    sys.stderr.write(str(e))
    sys.exit(return_code)


if __name__ == '__main__':
    main()

