# TODO:
# Threads: main, engine, gui
# Put parser in class
# Tempo as argparse option
# Debug options
# Handle errors
#   a = [], etc.
#   general parser and lexer errors
# Octava as property of part

import ply.lex as lex
import ply.yacc as yacc
import sys
from model import *
from midi import *

tokens = (
    'ID', 'ASSIGN', 'LSQUARE', 'RSQUARE',
    'LCURLY', 'RCURLY', 'EQ', 'NEQ',
    'PAUSE', 'COMMA', 'BECOMES', 'DOT',
    'NUMBER'
    )

t_ID        = r'[a-zA-Z][a-zA-Z0-9_]*'
t_ASSIGN    = r'='
t_LSQUARE   = r'\['
t_RSQUARE   = r'\]'
t_LCURLY    = r'\{'
t_RCURLY    = r'\}'
t_PAUSE     = r'_'
t_COMMA     = r','
t_BECOMES   = r'=>'
t_DOT       = r'\.'

t_ignore = ' \t'

def t_NUMBER(t):
    r'[-+]?\d+'
    t.value = int(t.value)
    return t

def t_EQ(t):
    r'=='
    t.value = Comparator.eq
    return t

def t_NEQ(t):
    r'!='
    t.value = Comparator.neq
    return t

def t_COMMENT(t):
    r'\#.*'
    pass

def t_newline(t):
    r'\n'
    t.lexer.lineno += 1

def t_error(t):
    print("Illegal character '%s'" %
          t.value[0])
    sys.exit(1)

lex.lex()


parts = {}
rules = []

def p_program(p):
    '''program : program statement
               | statement'''

def p_statement(p):
    '''statement : partassign
                 | propassign
                 | rule'''

def p_empty(p):
    'empty :'
    pass

def p_partassign(p):
    'partassign : ID ASSIGN notelist'
    parts[p[1]] = Part(p[1], p[3])

def p_notelist(p):
    'notelist : LSQUARE notes RSQUARE'
    p[0] = p[2]

def p_notes_list(p):
    'notes : note COMMA notes'
    p[0] = [p[1]] + p[3]

def p_notes_single(p):
    'notes : note'
    p[0] = [p[1]]

def p_notes_empty(p):
    'notes : empty'
    p[0] = []

def p_note_number(p):
    'note : NUMBER'
    note = p[1]
    if note < 0 or note > 127:
        raise Exception("Note values must lie between 0 and 127")
    p[0] = note

def p_note_pause(p):
    'note : PAUSE'
    p[0] = PAUSE

def p_property(p):
    'property : ID DOT ID'
    p[0] = {'part': parts[p[1]], 'prop': p[3]}

def p_propassign_number(p):
    'propassign : property ASSIGN NUMBER'
    part = p[1]['part']
    prop = p[1]['prop']
    value = p[3]
    part.set_property(prop, value)

def p_rule(p):
    'rule : lhs BECOMES rhs'
    rules.append(Rule(p[1], p[3]))

def p_lhs(p):
    'lhs : LCURLY clauses RCURLY'
    p[0] = p[2]

def p_clauses_list(p):
    'clauses : clause COMMA clauses'
    p[0] = [p[1]] + p[3]

def p_clauses_single(p):
    'clauses : clause'
    p[0] = [p[1]]

def p_clauses_empty(p):
    'clauses : empty'
    p[0] = []

def p_clause(p):
    'clause : indexed comparator subject'
    p[0] = Clause(p[1], p[2], p[3])

def p_indexed(p):
    'indexed : ID LSQUARE NUMBER RSQUARE'
    p[0] = Indexed(parts[p[1]], p[3])

def p_comparator(p):
    '''comparator : EQ
                  | NEQ'''
    p[0] = p[1]

def p_subject(p):
    '''subject : note
               | indexed'''
    p[0] = p[1]

def p_rhs(p):
    'rhs : LCURLY modifiers RCURLY'
    p[0] = p[2]

def p_modifiers_list(p):
    'modifiers : modifier COMMA modifiers'
    p[0] = [p[1]] + p[3]

def p_modifiers_single(p):
    'modifiers : modifier'
    p[0] = [p[1]]

def p_modifiers_empty(p):
    'modifiers : empty'
    p[0] = []

def p_modifier(p):
    'modifier : indexed ASSIGN subject'
    p[0] = Modifier(p[1], p[3])

def p_error(p):
    print "Syntax error on line %d, lexpos %d, token %s" % (p.lineno, p.lexpos, p.type)

yacc.yacc()

lines = ''.join(sys.stdin.readlines())
yacc.parse(lines)

engine = Engine(parts.values(), rules)
gui = Gui(parts, rules)
player = Player(120)
logger = None
sleep_time = seconds = (60.0 / self.bpm) * (self.subdivision * 4)

while True:
    midi_notes = engine.get_midi_notes()
    #engine.debug()

    for t, notes in midi_notes.iteritems():
        if gui:
            gui.step(t)
        for note in notes:
            player.noteon(note)
        time.sleep(sleep_time)
        for note in notes:
            player.noteoff(note)
    
    engine.iterate()
    if gui:
        log = engine.log
        gui.visualise_log(log)
