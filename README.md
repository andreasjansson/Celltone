Celltone
========

*A simple programming language for generative music composition using cellular automata*

Demo
----

To get a feel for what it is, there's a little demo up at http://demo.celltone-lang.com.

The language
------------

### Parts and rules ###

A Celltone program is made up of two things: a number of *parts* and
a number of *rules*. A part is a named list of notes and pauses, for 
example:

    p = [0, _, _, 4, _, _, 7, _, _]


Notes are numbers and pauses are underscores. The number 0 represents
a C, 4 is an E, and so on.

Rules are used to transform the parts. Example:

    {p[0] == 0, p[1] == _} => {p[0] = _, p[1] = 2}


This example rule would transform the part we defined earlier into

    p = [_, 2, _, 4, _, _, 7, _, _]

### Iterations and cyclicity ###

Rules are applied to parts in an iterative fashion. The length
of an iteration is by default the length of the longest part.
After each iteration the parts are updated based on the rule set.
Parts can be of different lengths, and they are played back
in a cycle.

For example, say we have the parts

    a = [0, _, 2, _]
    b = [4, _, _]


During iteration 1, `a` would play `[0, _, 2, _]`, and `b` would play `[4, _, _, 4]`. During iteration 2, `a` would play `[0, _, 2, _]`, but `b` would play `[_, _, 4, _]`.

### Rules in detail ###

The cyclicity of the parts also applies to the rules. Say we have the
parts from above, along with the rule

    {a[0] != _, b[0] != _} => {b[-1] = 7}


After the first iteration, the rule would match the first beat,
and the parts would now be

    a = [0, _, 2, _]
    b = [4, _, 7]


For the second iteration, `b` is shifted by one step, and the notes
played are now

    [0, _, 2, _] # a
    [_, 7, 4, _] # b


Rules are evaluated in the order they are defined in the source file.
Notes can match in the left hand side of many rules, but may only
be altered by the right hand side in one rule. For example, if we have

    p = [0, _, 2, 4]
    {p[0] == 2, p[1] != _} => {p[0] = _} # rule 1
    {p[0] == _} => {p[0] = 2, p[1] = 7}  # rule 2


both rules would match, but only rule 1 would get applied. This is
because the note at position 3 would have been modified by the
second rule, but it had already been modified by the first rule.

### Indexed parts ###

Not only can notes be indexed using the `x[+2]` syntax, parts can
also be indexed using the following syntax:

    {<0>[0] == <1>[0], <0>[1] != _} => {<0>[0] = 1, <1>[1] = _}

For the index to have meaning, parts need to be ordered. By default
parts are ordered in the order they are defined, but the global
propoerty `<partorder>` can be used to specify explicit ordering:

    <partorder> = [a, c, b, d]
    
### Part properties ###

Parts have properties that can be set (but currently not changed)
in the source file. At the moment, `channel`, `velocity`,
`octava` and `transpose` are supported. Example:

    a = [0, _, 4, _, 9]
    a.channel = 4
    a.velocity = 90
    a.octava = 5

### Global properties ###

Global properties affect the piece as a whole. Currently the
available properties are `<tempo>`, `<iterlength>`, `<subdiv>`, `<transpose>` and `<partorder>`. Example:

    <tempo> = 124
    <subdiv> = 16


### Comments ###

Comments start with `#` and end at the end of the line.


Installation
------------

Installation is pretty straight forward -- at least once you have pyPortMidi installed.

First, make sure you have the python, python-setuptools and portmidi packages.
On Linux you also need the ALSA development packages. Then, download pyPortMidi. I use
aalex's fork on BitBucket: https://bitbucket.org/aalex/pyportmidi/downloads/python-portmidi-0.0.7.tar.gz
In the python-portmidi directory, run `sudo python setup.py install`. If this fails, it should hint
at what went wrong. Maybe you need to run `sudo easy_install pyrex`? 
There's good documentation at https://bitbucket.org/aalex/pyportmidi/wiki/Home
on how to get pyPortMidi working.

When that is done, download the Celltone sources, cd into the Celltone directory, and run `sudo python setup.py install`.

Running Celltone
----------------

Once installed, run Celltone by giving it a filename as an argument

    celltone examples/bubblesort.ct
    
To see the available command line options, type

    celltone -h

Debug output
------------

To enable debug output, add `-v`, `-vv` or `-vvv` as an argument.
`-v` will output the current parts and their notes, `-vv` will
additionally output the rules that were used in this generation, and
`-vvv` will also indicate which notes were used in the application
of the rule.

MIDI output
-----------

By default, output is fed to the default MIDI device in realtime,
using PortMidi. Use a tool like pmdefaults or
qjackctl to route the MIDI output to some MIDI input device. 

You can also use Celltone to generate MIDI files
offline using the `--file` command line flag.

Runtime source file updates
---------------------------

Celltone can be used as a performance tool, by specifying the
`--update` command line flag. This allows you to update the source
file in realtime, during playback.

