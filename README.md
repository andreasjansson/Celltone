Celltone
========

*A simple programming language for generative music composition using cellular automata*


Installation
------------

Download the source and run

<code>
python setup.py install
</code>

That should hopefully download all the dependencies.


Running Celltone
----------------

Once installed, run Celltone by giving it a filename as an argument

<code>
celltone examples/bubblesort.ct
</code>

To enable debug output, add `-v`, `-vv` or `-vvv` as an argument.
`-v` will output the current parts and their notes, `-vv` will
additionally output the rules that were used in this generation, and
`-vvv` will also indicate which notes were used in the application
of the rule.


The language
------------

### Parts and rules ###

A Celltone program is made up of two things: a number of *parts* and
a number of *rules*. A part is a named list of notes and pauses, for 
example:

<code>
p = [0, _, _, 4, _, _, 7, _, _]
</code>

Notes are numbers and pauses are underscores. The number 0 represents
a C, 4 is an E, and so on.

Rules are used to transform the parts. Example:

<code>
{p[0] == 0, p[1] == _} => {p[0] = _, p[1] = 2}
</code>

This example rule would transform the part we defined earlier into

<code>
p = [_, 2, _, 4, _, _, 7, _, _]
</code>


### Iterations and cyclicity ###

Rules are applied to parts in an iterative fashion. The length
of an iteration is by default the length of the longest part.
After each iteration the parts are updated based on the rule set.
Parts can be of different lengths, and they are played back
in a cycle.

For example, say we have the parts

<code>
a = [0, _, 2, _]
b = [4, _, _]
</code>

During iteration 1, `a` would play `[0, _, 2, _]`, and `b` would play `[4, _, _, 4]`. During iteration 2, `a` would play `[0, _, 2, _]`, but `b` would play `[_, _, 4, _]`.

### Rules in detail ###

The cyclicity of the parts also applies to the rules. Say we have the
parts from above, along with the rule

<code>
{a[0] != _, b[0] != _} => {b[-1] = 7}
</code>

After the first iteration, the rule would match the first beat,
and the parts would now be

<code>
a = [0, _, 2, _]
b = [4, _, 7]
</code>

For the second iteration, `b` is shifted by one step, and the notes
played are now

<code>
[0, _, 2, _] # a
[_, 7, 4, _] # b
</code>

Rules are evaluated in the order they are defined in the source file.
Notes can match in the left hand side of many rules, but may only
be altered by the right hand side in one rule. For example, if we have

<code>
p = [0, _, 2, 4]
{p[0] == 2, p[1] != _} => {p[0] = _} # rule 1
{p[0] == _} => {p[0] = 2, p[1] = 7}  # rule 2
</code>

both rules would match, but only rule 1 would get applied. This is
because the note at position 3 would have been modified by the
second rule, but it had already been modified by the first rule.


### Part properties ###

Parts have properties that can be set (but currently not changed)
in the source file. At the moment, `channel`, `velocity` and
`octava` are supported. Example:

<code>
a = [0, _, 4, _, 9]
a.channel = 4
a.velocity = 90
a.octava = 5
</code>


### Global properties ###

Global properties affect the piece as a whole. Currently the
available properties are `<tempo>` and `<subdiv>`. Example:

<code>
<tempo> = 124
<subdiv> = 16
</code>


### Comments ###

Comments start with `#` and end at the end of the line.
