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

