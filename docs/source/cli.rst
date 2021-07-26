.. _cli:

######################
Command Line Interface
######################

The command line tool comes with several subcommands. For each command, you can see the help
text with the command

.. code-block:: shell
   
   bionetgen subcommand -h

Run
===

This subcommand simply runs a model:

.. code-block:: shell
   
   bionetgen run -i mymodel.bngl -o output_folder

This will run :code:`mymodel.bngl` under the folder :code:`output_folder`.
If no output folder is specified, then the temporary folder used while running the subcommand will be deleted upon completion.

Plot
====

This subcommand allows you to make a simple plot from a gdat/cdat file:

.. code-block:: shell
   
   bionetgen plot -i mymodel.gdat -o gdat_plot.png

You can see all the available options by running :code:`bionetgen plot -h` 

.. code-block:: shell
   
   optional arguments:
      -h, --help            show this help message and exit
      -i INPUT, --input INPUT
                              Path to .gdat/.cdat file to use plot
      -o OUTPUT, --output OUTPUT
                              Optional path for the plot (default:
                              "$model_name.png")
      --legend              To plot the legend or not (default: False)
      --xmin XMIN           x-axis minimum (default: determined from data)
      --xmax XMAX           x-axis maximum (default: determined from data)
      --ymin YMIN           y-axis minimum (default: determined from data)
      --ymax YMAX           y-axis maximum (default: determined from data)
      --xlabel XLABEL       x-axis label (default: time)
      --ylabel YLABEL       y-axis label (default: concentration)
      --title TITLE         title of plot (default: determined from input file)

Notebook
========

This subcommand is in its early stages of development. The subcommand is used to generate a
simple `Jupyter notebook <https://jupyter.org/>`_. You can also give your model as an argument
and the resulting notebook will be ready to load in your model using PyBioNetGen library. 

.. code-block:: shell
   
   bionetgen notebook -i mymodel.bngl -o mynotebook.ipynb