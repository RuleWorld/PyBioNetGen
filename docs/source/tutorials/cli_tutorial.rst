.. cli_tut:

############
CLI Tutorial
############

This tutorial shows how to use PyBioNetGen's command line interface to run and plot a simple BNGL model,
as well as how to create a simple Jupyter notebook containing the model, using the simple "SIR.bngl"
model as an example.

Getting Started
===============

Make sure you have PyBioNetGen properly installed by running

.. code_block:: shell

    bionetgen -h

If this command doesn't print out help information, install PyBioNetGen with

.. code_block:: shell

    pip install bionetgen


Running a Model
===============

To first run your model in a new or existing folder called "SIR_folder", use the :code:`run` subcommand:

.. code-block:: shell

    bionetgen run -i SIR.bngl -o SIR_folder

Plotting a Model
================

To simply plot the gdat or cdat file, use the :code:`plot` subcommand with the appropriate file:

.. code-block:: shell

    bionetgen plot -i SIR.gdat

