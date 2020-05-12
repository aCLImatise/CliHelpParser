Changelog
=========
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
