from model import *
from parser import Parser
from midi import Player
import sys

def main():
    text = ''.join(sys.stdin.readlines())
    parser = Parser()
    parts, rules, config = parser.parse(text)
    engine = Engine(parts, rules)
    iterlength = config.get('iterlength')
    if iterlength is not None:
        engine.iteration_length = iterlength
    player = Player(config.get('tempo'), config.get('subdiv'))

    while True:
        midi_notes = engine.get_midi_notes()
        player_thread = player.play(midi_notes)
        engine.iterate()
        engine.debug()
        player_thread.join()

if __name__ == '__main__':
    main()
