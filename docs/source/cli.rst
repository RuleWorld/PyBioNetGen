.. _cli:

######################
Command line Interface
######################

The command line tool comes with several subcommands. For each command you can see the help
text with the command

.. code-block:: shell
   
   bionetgen subcommand -h

Run
===

You can use this subcommand to run a model with

.. code-block:: shell
   
   bionetgen run -i mymodel.bngl -o output_folder

which will run :code:`mymodel.bngl` under the folder :code:`output_folder`. 

Plot
====

This can plot.

.. code-block:: shell
   
   bionetgen plot 

Notebook
========

Generates a Jupyter notebook.

.. code-block:: shell
   
   bionetgen notebook