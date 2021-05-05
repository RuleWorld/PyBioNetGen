.. _library:

#######
Library
#######

PyBioNetGen also comes with a library that allows you to programatically run and do simple 
modifications of BNGL models. 

run
===

This method allows you to do a simple run of a BNGL model and returns the results as 
`numpy record arrays <https://numpy.org/doc/stable/reference/generated/numpy.recarray.html>`_.

.. code-block:: python

   import bionetgen
   result = bionetgen.run("mymodel.bngl", output="myfolder")
   result["mymodel"] # this will contain the gdat results of the run

:ref:`bngmodel`
===============

This method allows you to load in a model into a python object. 

.. code-block:: python

   import bionetgen
   model = bionetgen.bngmodel("mymodel.bngl") # generates BNG-XML and reads it
   print(model)

Please see :ref:`bngmodel` for more all the features this object supports.

bngmodel.setup_simulator
------------------------

This method allows you to get a `libroadrunner <http://libroadrunner.org/>`_ simulator 
of the loaded model. 

.. code-block:: python

   import bionetgen
   model = bionetgen.bngmodel("mymodel.bngl") # generates BNG-XML and reads it
   librr_simulator = model.setup_simulator().simulator
   librr_simulator.simulate(0,1,10) # librr_simulator is the simulator object 

This is an easy way to generate data for analyses of your model using Python.