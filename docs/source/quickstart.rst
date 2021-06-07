.. _quickstart:

##########
Quickstart
##########

Installation
============

You will need both python (3.7 and above) and perl installed. Once both are available you can use the following :code:`pip` command to install PyBioNetGen

.. code-block:: shell

    pip install bionetgen

which comes with the latest version of `BioNetGen <https://bionetgen.org>`_. Please note that,
at the moment, PyBioNetGen does not support Atomizer but eventually will.

Basic usage
===========

After installation complete you can test to see if PyBioNetGen is properly installed with

.. code-block:: shell

   bionetgen -h

if this command prints out help, the command line tool is installed.

You can use PyBioNetGen to simply run a BNGL model

.. code-block:: shell

   bionetgen run -i mymodel.bngl -o output_folder

which will create :code:`output_folder` and run :code:`mymodel.bngl` inside that folder. For 
more information on how to use PyBioNetGen please see :ref:`cli` and :ref:`library`.
