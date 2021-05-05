.. _bngmodel:

########
bngmodel
########

Basic usage
===========

This is designed to be a pythonic object representing the BNGL model given. It 
currently has some limited options to modify the model. You can load the model
object using

.. code-block:: python

   import bionetgen
   model = bionetgen.bngmodel("mymodel.bngl") # generates BNG-XML and reads it
   

The underlying code will attempt to generate a BNG-XML of the model which it then 
reads to generate this object. 

One core principle of this object is that the object and every object associated with 
it can be converted to a string to get the BNGL string of the object itself. For 
example

.. code-block:: python
   :linenos:

   print(model) # this prints the entire model
   print(model.observables) # prints the observables block
   print(model.parameters) # prints the parameters block
   model.parameters.k = 10 # sets parameter k to 10
   print(model.parameters) # block updated to reflect change
   
The BNGL string is dynamically generated and not just returning the block string from 
the original model. This allows for making simple changes to your model, e.g.

.. code-block:: python
   :linenos:

   for i in range(10):
       model.parameters.k = i
       with open("param_k_{}.bngl".format(i), "w") as f:
           f.write(str(model))

This will write 10 models with different k parameters.

Blocks
======

All blocks that are active can be seen with print(model.active_blocks). Currently supported 
blocks are 

- Parameters
- Compartments
- Molecule types
- Species (or seed species)
- Observables
- Functions 
- Reaction rules

PyBioNetGen bngmodel also recognizes actions within the model but discards them upon loading (this
will eventually be optional). All bionetgen features will eventually be supported by this library, 
including every valid BNGL block.

Blocks also act pythonic and act like other python objects

.. code-block:: python
   :linenos:

   for param in model.parameters:
       print("parameter name: {}".format(param))
       print("parameter value: {}".format(model.parameters[param]))
   
   for obs in model.observables:
       obs_val = model.observables[obs]
       print("observable name: {}".format(obs))
       print("observable type: {}".format(obs_val[0]))
       print("observable pattern: {}".format(obs_val[1]))

   for spec in model.species:
       spec_count = model.species[spec]
       print("species name: {}".format(spec))
       print("species count: {}".format(spec_count))
       print("molecules in species: {}".format(spec.molecules))
       
The following sections will detail how each block behaves 

Parameters
----------

Parameters are a list of names and values associated with those names. Values can be either
floating point numbers or string expressions. 

.. code-block:: 
   :linenos:

   model.parameters


Compartments
------------

.. code-block:: 
   :linenos:

   model.compartments

Molecule types
--------------

.. code-block:: 
   :linenos:

   model.moltypes

Species
-------

.. code-block:: 
   :linenos:

   model.species

Observables
-----------

.. code-block:: 
   :linenos:

   model.observables

Functions
---------

.. code-block:: 
   :linenos:

   model.functions

Reaction rules
--------------

.. code-block:: 
   :linenos:

   model.rules