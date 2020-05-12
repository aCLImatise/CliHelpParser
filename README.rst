Acclimatise
***********
For the full documentation, refer to the `Github Pages Website
<https://aclimatise.github.io/CliHelpParser/>`_.

======================================================================

Acclimatise is a Python library and command-line utility for parsing the help output
of a command-line tool and then outputting a description of the tool in a more
structured format, for example a
`Common Workflow Language tool definition <https://www.commonwl.org/v1.1/CommandLineTool.html>`_.

Currently Acclimatise supports both `CWL <https://www.commonwl.org/>`_ and
`WDL <https://openwdl.org/>`_ outputs, but other formats will be considered in the future, especially pull
requests to support them.

Example
-------

Lets say you want to create a CWL workflow containing the common Unix ``wc`` (word count)
utility. Running ``wc --help`` returns:

.. code-block::

   Usage: wc [OPTION]... [FILE]...
     or: wc [OPTION]... --files0-from=F
   Print newline, word, and byte counts for each FILE, and a total line if
   more than one FILE is specified.  A word is a non-zero-length sequence of
   characters delimited by white space.

   With no FILE, or when FILE is -, read standard input.

   The options below may be used to select which counts are printed, always in
   the following order: newline, word, character, byte, maximum line length.
     -c, --bytes            print the byte counts
     -m, --chars            print the character counts
     -l, --lines            print the newline counts
         --files0-from=F    read input from the files specified by
                              NUL-terminated names in file F;
                              If F is - then read names from standard input
     -L, --max-line-length  print the maximum display width
     -w, --words            print the word counts
         --help display this help and exit
         --version output version information and exit

   GNU coreutils online help: <http://www.gnu.org/software/coreutils/>
   Full documentation at: <http://www.gnu.org/software/coreutils/wc>
   or available locally via: info '(coreutils) wc invocation'

If you run ``acclimatise explore wc``, which means "parse the wc command and all subcommands",
you'll end up with the following files in your current directory:

* ``wc.cwl``
* ``wc.wdl``
* ``wc.yml``

These are representations of the command ``wc`` in 3 different formats. If you look at ``wc.wdl``, you'll see that it
contains a WDL-compatible tool definition for ``wc``:

.. code-block:: wdl
    version 1.0
    task Wc {
      input {
        Boolean bytes
        Boolean chars
        Boolean lines
        String files__from
        Boolean max_line_length
        Boolean words
      }
      command <<<
        wc \
          ~{true="--bytes" false="" bytes} \
          ~{true="--chars" false="" chars} \
          ~{true="--lines" false="" lines} \
          ~{if defined(files__from) then ("--files0-from " +  '"' + files__from + '"') else ""} \
          ~{true="--max-line-length" false="" max_line_length} \
          ~{true="--words" false="" words}
      >>>
    }
