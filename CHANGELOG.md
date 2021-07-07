# BioNetGen CLI Change History

## 0.0.1
Working CLI.

## 0.0.2 
Added Mac/Linux supported, latest BNG version downloading, working environment variable setup. 

## 0.0.3
CI and everything working

## 0.0.4
The library now returns results and doesn't need an output folder

## 0.0.5
Now bundling Linux/Mac binaries with the package, removed translator binary from the bundle to keep package size within limits

## 0.0.6
Bugfixing useless line that crashes the CLI

## 0.0.7
Adding notebook subcommand for testing a Jupyter notebook, added a starter notebook

## 0.0.8
Adding Windows support

## 0.0.9
Adding a better notebook, windows support tests done

## 0.1.0
Notebook command now writes a new one in the folder that it was called from, added a template to also allow for -i to be used for the resulting notebook

## 0.1.1
Adding XML-API to the library. Currently it is essentially completely separate

## 0.1.2
some bugfixes to XML-API

## 0.1.3
Adding simulator interface

## 0.1.4
simulator bugfixes

## 0.1.5
better simulator setup, new defaults system and by default supress stdout 

## 0.1.6
uptick to get BNG 2.5.2

## 0.1.7
uptick for changed xmltodict version to allow later pythons to install the library

## 0.1.8
adding rudimentary plotting for gdat/cdat files

## 0.1.9
major changes to how the command line is called, going full subcommand based structure

## 0.2.0
minor behavior change to plot subcommand --legend option

## 0.2.1
bugfix to previous change

## 0.2.2
added basic .scan file plotting to the plot subcommand

## 0.2.3
BNG2.pl stdout now pipes correctly to actual stdout and can be adjusted via configuraion files

## 0.2.4
Adding documentation, rewriting temporary folder and file handling to use TemporaryDirectory and Temporary file respectively so that these work correctly on Windows. 

## 0.2.5
Fixing a bug that was caused by method renaming

## 0.2.6
Notebook subcommand now by default doesn't open the notebook using nbopen, an argument allows you
to do so.

## 0.2.7
Reorganization of library functionality and library side now has access to configuration parsing from cement framework. Published on PyPI

## 0.2.9
Updating BioNetGen version to 2.6.0

## 0.3.0
Massive model object restructuring complete and XML parsing is separated from model object. Fixed XML parsing of certain features like constant species. 

## 0.3.1
Various changes fixing issues #1 and #7. BNG2.pl output is immediately piped out stdout.

## 0.3.2
Updated BNGResult object to be user friendly, updated OrderedDict import to try collections library.