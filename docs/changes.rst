Changelog
=========
0.1.4 (2020-05-)
------------------
* Choose best command using length of help text, if everything else is equal

0.1.3 (2020-05-15)
------------------
* ``Command`` types now contain a ``help_text`` field which records the string that was used to generate them. This should enable efficient re-parsing, and can also be displayed downstream by BaseCamp
* Rewrite tests into a parametrized, consolidated end-to-end test
* Fix "OPTIONS" being considered a positional argument, when really it's a placeholder for flags
* Remove positional arguments that precede the main command, so `dotnet Pisces.dll` will be removed from the entire
command

0.1.2 (2020-05-15)
------------------
* Generating YAML output now produces one file for each subcommand, to match other converters

0.1.1 (2020-05-13)
------------------
* Make ``explore -o`` flag default to current working directory, for simplicity
* Updated the readme
* Add installation instructions

0.1.0 (2020-05-13)
------------------
* Fix the doubled variable names like ``bytesBytes``
* Smarter POS-based algorithm for generating names from descriptions
* Automatically choose a description based name when we have only short named flags like ``-n``
* Add changelog
* Add comprehensive testing for CWL and WDL generation
* Fix for variable names with symbols in them
* Use regex library for faster and more concise regex
