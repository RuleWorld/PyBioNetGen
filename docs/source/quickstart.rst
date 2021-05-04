.. _quickstart:

##########
Quickstart
##########

Installation
============

You can use :code:`pip` to install PyBioNetGen 

.. code-block:: shell

    pip install bionetgen

which also installs the latest version of `BioNetGen <https://bionetgen.org>`_.

Usage
=====

After installation complete you can test to see if it's properly installed with

.. code-block:: shell

   bionetgen -h

if this command prints out help, the command line tool is installed.

You can use PyBioNetGen to simply run a BNGL model

.. code-block:: shell

   bionetgen run -i mymodel.bngl -o output_folder

which will create :code:`output_folder` and run :code:`mymodel.bngl` inside that folder. For 
more information on how to use PyBioNetGen please see :ref:`cli` and :ref:`library`.