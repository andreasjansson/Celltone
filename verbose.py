import os
import textwrap

DEFAULT_WIDTH = 80
SPACES = 5

width = DEFAULT_WIDTH

class Verbose:

    def __init__(self, verbosity = 1):
        self.verbosity = verbosity

    def print_parts(self, parts):
        find_width()
        if self.verbosity < 1:
            return

        for name in sorted(parts.keys()):
            print(PartFormatter(parts[name]))
        print('\n')

    def print_log(self, items):
        find_width()
        if self.verbosity < 2:
            return

        for item in items:
            print(RuleFormatter(item, self.verbosity >= 3))
        print('')
            
class PartFormatter:

    def __init__(self, part):
        self.lines = wrap(str(part))

    def __str__(self):
        return '\n'.join(self.lines)

class RuleFormatter:

    def __init__(self, item, verbose = False):
        self.item = item
        self.verbose = verbose
        self.lines = ''

    def format(self):
        self.format_rule()
        if self.verbose:
            self.format_clauses()
            self.format_modifiers()

    def format_rule(self):
        rule = self.item.rule
        lines += wrap(str(rule))
        
    def format_lhs(self):
        clauses = self.item.rule.lhs
        beat = self.item.beat_before
        for clause in clauses:
            pass

    def __str__(self):
        return '\n'.join(self.lines)
            

def wrap(text):
    lines = textwrap.wrap(text, width, subsequent_indent = ' ' * SPACES,
                          break_on_hyphens = False)
    return lines
    

def find_width():
    global width
    size = os.popen('stty size 2> /dev/null', 'r').read()
    if not size or ' ' not in size:
        width = DEFAULT_WIDTH
    else:
        width = int(size.split()[1])

