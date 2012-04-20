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


from model import Engine, logger
import parser
import sys
import signal
import time
import os
import os.path
import midi

celltone_home = os.path.expanduser('~/.celltone')

class Celltone(object):

    def __init__(self, code, verbosity = 0):
        if not os.path.exists(celltone_home):
            os.mkdir(celltone_home)

        self.parser = parser.Parser()
        if verbosity > 0:
            from verbose import Verbose
            self.verbose = Verbose(verbosity)
        else:
            self.verbose = None

        signal.signal(signal.SIGINT, self.exit)

        self.leftover_midi_notes = None
        self.is_playing = False

        self.player = None
        self.engine = None
        self.set_code(code)

    def exit(self, signal = None, frame = None):
        self.stop()

        # harmless exceptions may be thrown here. surpress
        class Devnull:
            def write(self, _): pass
        sys.stderr = Devnull()
        sys.exit(0)

    def set_code(self, code):
        if code:
            try:
                parts, rules, part_order, config = self.parser.parse(code)
            except parser.ParseError as e:
                die(str(e))
        else:
            die('Error: Empty input')

        if config.get('partorder'):
            part_order = config.get('partorder')

        self.engine = Engine(parts, rules, part_order)
        iterlength = config.get('iterlength')
        if iterlength is not None:
            self.engine.iteration_length = iterlength

        self.player = midi.Player(config.get('tempo'), config.get('subdiv'))

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
        if not len(self.engine.parts):
            die('Error: No parts to play')
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

    try:
        if not args.filename or args.filename == '-':
            code = ''.join(sys.stdin.readlines())
        else:
            if not os.path.exists(args.filename):
                die('Error: No such file \'%s\'' % args.filename)
            with open(args.filename) as f:
                code = ''.join(f.readlines())
    except KeyboardInterrupt:
        sys.exit(0)

    celltone = Celltone(code, verbosity)
    celltone.play()
    celltone.loop()


def die(string, return_code = 1):
    sys.stderr.write(string + '\n')
    sys.exit(return_code)

def warning(string):
    sys.stderr.write('***** WARNING: ' + string + ' *****\n')

if __name__ == '__main__':
    main()

