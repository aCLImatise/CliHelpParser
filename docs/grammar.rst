Grammar
=======

Internally, aCLImatise uses a `Parsing Expression Grammar <https://en.wikipedia.org/wiki/Parsing_expression_grammar>`_,
which is a class of recursive grammar used to parse programming languages. This grammar is expressed and parsed using
the `PyParsing <https://github.com/pyparsing/pyparsing>`_ Python library. To help visualise the grammar used to parse
command-line help, here is a `Railroad Diagram <https://en.wikipedia.org/wiki/Syntax_diagram>`_ generated using
PyParsing.

The "terminal" nodes (circular) are either:

* In quotes, e.g. ``':'``, which indicates a literal string
* In the form ``W:(start, body)``, e.g. ``W:(0-9@-Za-z, \--9@-Z\\_a-z|)``, which indicates a word where the first character comes from the ``start`` list of characters, and the remaining characters come from the ``body`` characters
* In the form ``Re: pattern``, which indicates a regular expression pattern used to match this terminal
* Whitespace nodes, e.g. ``<SP><TAB><CR><LF>``, which list the types of whitespace being parsed by that terminal
* Certain other special nodes like ``Empty``, and ``LineStart`` which match based on custom code. Where possible, these are annotated with what they are designed to match, for example ``UnIndent`` matches an unindent in the input file.

The "non-terminal" nodes (square) refer to subsections of the diagram, which are spelled-out under the subheading with
the same name.

To read the diagram, start with ``FlagList``, the start node, and from there follow the lines along any branch of the path that goes forward (although some paths end up turning backwards to indicate loops). Any string that matches the sequence of tokens you encounter along that path will be parsed by the grammar.

.. raw:: html
   :file: _static/railroad.html
