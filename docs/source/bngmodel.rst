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

Parameters are a list of names and values associated with those names. Parameters block also
stores the parameter expressions in case they are written as functions in the original model.

.. code-block:: 
   :linenos:

   # let's say we have a parameter k
   model.parameters["k"] = 10 # this is the parameter value
   model.parameters.k = 10 # this is also the parameter value 
   model.parameters.expressions["k"] # this is the parameter expression
   

Compartments
------------

.. code-block:: 
   :linenos:

   model.compartments

Molecule types
--------------

.. code-block:: 
   :linenos:

   # let's say we have a molecule type "X()" as the first one
   X_obj = model.moltypes[0] # this is the object for "X()" molecule type
   print(X_obj) # will print the molecule type string
   X_obj.add_component("p", states=["0","1"]) # adds a component with states
   print(X_obj) # prints "X(p~0~1)" now

Species
-------

.. code-block:: 
   :linenos:

   # let's say we have a species with pattern "X()"
   species_obj = model.species[0] # this is the species object
   print(species_obj) # prints the pattern
   count = model.species[species_obj] # this is the starting count of the species
   count = model.species["X()"] # this is the starting count of the species
   molecules = species_obj.molecules # this is the list of molecules in the pattern
   compartment = species_obj.compartment # this is the overall compartment of the species
   label = species_obj.label # this is the overall label of the species

Observables
-----------

Observables are made up of species patterns.

.. code-block:: 
   :linenos:

   # let's say we have a observable with string "Molecules X_phos X(p~1)"
   obs_obj = model.observables[0] # this is the observable object
   print(obs_obj) # prints the observable patterns, in this case X(p~1)
   obs_list = model.observables["X_phos"] # this returns a list of two items
   type, obs_obj = obs_list # first one is the type, "Molecules" and second one is the object again
   patterns = obs_obj.patterns # this is the list of patterns in the observable string

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