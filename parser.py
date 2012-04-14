# TODO:
# Run main, engine and midi player in separate threads
# Put parser in class
# Tempo as argparse option
# Debug options
# Handle errors
#   a = [], etc.

import ply.lex as lex
import ply.yacc as yacc
import sys
from model import *
from midi import *

tokens = (
    'ID', 'ASSIGN', 'LSQUARE', 'RSQUARE',
    'LCURLY', 'RCURLY', 'EQ', 'NEQ',
    'LT', 'LTE', 'GT', 'GTE',
    'PAUSE', 'COMMA', 'BECOMES', 'DOT',
    'NUMBER', 'OPTION',
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

def t_OPTION(t):
    r'<[a-zA-Z][a-zA-Z0-9_]*>'
    t.value = t.value[1:-1]
    return t

def t_EQ(t):
    r'=='
    t.value = CompEQ()
    return t

def t_NEQ(t):
    r'!='
    t.value = CompNEQ()
    return t

def t_LT(t):
    r'<'
    t.value = CompLT()
    return t

def t_LTE(t):
    r'<='
    t.value = CompLTE()
    return t

def t_GT(t):
    r'>'
    t.value = CompGT()
    return t

def t_GTE(t):
    r'>='
    t.value = CompGTE()
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
config = Config()

def p_program(p):
    '''program : program statement
               | statement'''

def p_statement(p):
    '''statement : partassign
                 | propassign
                 | rule
                 | confassign'''

def p_empty(p):
    'empty :'
    pass

def p_partassign(p):
    'partassign : ID ASSIGN notelist'
    if p[1] in parts:
        raise Exception('Cannot redefine part: ' + p[1])
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
                  | NEQ
                  | LT
                  | LTE
                  | GT
                  | GTE'''
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

def p_modifier_assign(p):
    'modifier : indexed ASSIGN subject'
    p[0] = Modifier(p[1], p[3])

def p_modifier_touch(p):
    'modifier : indexed'
    p[0] = Modifier(p[1], p[1])

def p_confassign_number(p):
    'confassign : OPTION ASSIGN NUMBER'
    config.set(p[1], p[3])

def p_error(p):
    print "Syntax error on line %d, lexpos %d, token %s" % (p.lineno, p.lexpos, p.type)
    sys.exit(1)

yacc.yacc()

lines = ''.join(sys.stdin.readlines())
yacc.parse(lines)

engine = Engine(parts.values(), rules)
iterlength = config.get('iterlength')
if iterlength is not None:
    engine.iteration_length = config.get('iterlength')

player = Player(config.get('tempo'), config.get('subdiv'))

while True:
    midi_notes = engine.get_midi_notes()
    engine.debug()
    player.play(midi_notes)
    engine.iterate()
