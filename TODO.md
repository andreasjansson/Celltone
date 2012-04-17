TODO
====

*An unstructured roadmap of features about to built.*


Indexed parts
-------------

Support the syntax

    {<0>[0] == <1>[0], <0>[-1] == x[0]} => {<0>[0] = _, <1>[0] = <-1>[0]}

where `<0>` is an indexed part. This means that there needs to be an
inherent ordering of parts. This can be solved by implicitly ordering
parts in the order they are defined, and providing a global `<partorder>`
property for explicit ordering:

    <partorder> = [a, b, x, d]
    
Indexing is cyclic as it is for notes.

(The reason for the angle bracket syntax is that angle brackets are used
in the global properties and generally mean something not part-specific.
Another reason is that I wanted a syntax that doesn't create expectations
of more expressive constructs. For example, if there was a special variable,
`@`, and notes could were indexed `@[0][0]`, one would assume that the
language eventually would support arbitrary variables. By using a different
syntax for parts, that creates a healthy constraint that, amongst other
things, means that the language will never be more than 2-dimensional,
and will never have variables.)


Transposition
-------------

Support both

    a.transpose = 3
    
and

    <transpose> = -2


Build script
------------

The setup.py script should be a one-step installer. At the moment,
pyPortMidi fails to build, and needs to be installed separately. It's
a bit of a mess.


Metaprogramming
---------------

Not a language feature as such, but I want to explore what can be done
when using a templating language such as erb to generate Celltone.
