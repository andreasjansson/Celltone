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


import ply.lex as lex
import ply.yacc as yacc
import sys
from model import *

tokens = (
    'ID', 'ASSIGN', 'LSQUARE', 'RSQUARE',
    'LCURLY', 'RCURLY', 'EQ', 'NEQ',
    'LT', 'LTE', 'GT', 'GTE',
    'PAUSE', 'COMMA', 'BECOMES', 'DOT',
    'NUMBER', 'OPTION', 'PARTINDEX',
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

def t_PARTINDEX(t):
    r'<[-+]?\d+>'
    t.value = int(t.value[1:-1])
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
    raise SyntaxError(t.lineno, "Illegal character '%s'" % t.value[0])



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
        raise SemanticError(p.lineno(1), "Cannot redefine part '%s'" % p[1])
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

def p_notes_empty_error(p):
    'notes : empty'
    raise SemanticError(p.lineno(1), 'Empty note lists are not permitted')

def p_note_number(p):
    'note : NUMBER'
    p[0] = p[1]

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
    try:
        part.set_property(prop, value)
    except Exception as e:
        raise SemanticError(p.lineno(2), str(e))

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
    'clause : moditem comparator subject'
    p[0] = Clause(p[1], p[2], p[3])

def p_indexed(p):
    'indexed : ID LSQUARE NUMBER RSQUARE'
    if p[1] not in parts:
        raise SemanticError(p.lineno(1), 'Undefined part \'%s\'' % p[1])
    p[0] = Indexed(parts[p[1]], p[3])

def p_partindexed(p):
    'partindexed : PARTINDEX LSQUARE NUMBER RSQUARE'
    p[0] = PartIndexed(p[1], p[3])

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
               | indexed
               | partindexed'''
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
    'modifier : moditem ASSIGN subject'
    p[0] = Modifier(p[1], p[3])

def p_modifier_touch(p):
    'modifier : moditem'
    p[0] = Modifier(p[1], p[1])

# TODO: better name
def p_moditem(p):
    '''moditem : indexed
               | partindexed'''
    p[0] = p[1]

def p_confassign(p):
    '''confassign : OPTION ASSIGN NUMBER
                  | OPTION ASSIGN partlist'''
    try:
        config.set(p[1], p[3])
    except Exception as e:
        raise SemanticError(p.lineno(1), str(e))

def p_partlist(p):
    'partlist : LSQUARE parts RSQUARE'
    p[0] = p[2]

def p_parts_list(p):
    'parts : ID COMMA parts'
    p[0] = [p[1]] + p[3]

def p_parts_single(p):
    'parts : ID'
    p[0] = parts[p[1]]

def p_parts_empty_error(p):
    'parts : empty'
    raise SemanticError(p.lineno(1), 'Empty part lists are not permitted')


def p_error(p):
    if p:
        raise SyntaxError(p.lineno)
    else:
        raise ParseError('Syntax error near end of file')

class Parser:

    def __init__(self):
        lex.lex()
        from celltone import celltone_home
        yacc.yacc(debug = 0, tabmodule = 'ply_parsetab', outputdir = celltone_home)

    def parse(self, code):
        yacc.parse(code)
        return (parts, rules, config)

class ParseError(Exception):
    pass

class SyntaxError(ParseError):
    def __init__(self, lineno, info = None):
        message = "Syntax error on line %d" % lineno
        if info:
            message += ': ' + info
        ParseError.__init__(self, message)

class SemanticError(ParseError):
    def __init__(self, lineno, info = None):
        message = "Error on line %d" % lineno
        if info:
            message += ': ' + info
        ParseError.__init__(self, message)

def is_midi_number(n):
    return n >= 0 and n <= 127

