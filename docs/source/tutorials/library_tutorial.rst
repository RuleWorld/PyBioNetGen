.. lib_tut:

################
Library Tutorial
################

This tutorial shows how to use PyBioNetGen's library to run a simple BNGL model (SIR.bngl), plot the results, 
and manipulate a model object.

Before using the library, it must be imported:

.. code-block:: python

    import bionetgen

Running a Model
===============

The :code:`run` method can be used to simply run a BNGL model.

.. code-block:: python

   result = bionetgen.run("SIR.bngl")

Optionally, the results can be saved in a new or existing folder.

.. code-block:: python

    result = bionetgen.run("SIR.bngl", out = "SIR_folder")

To view the resulting gdats of the model, use the :code:`gdat` attribute:

.. code-block:: python

    result.gdats["SIR"][:10]

Similarly, to view the resulting cdats of the model, use the :code:`cdat` attribute:

.. code-block:: python

    result.cdats["SIR"][:10]

Plotting Results
================

To plot the gdat record array, matplotlib will be needed:

.. code-block:: python

    import matplotlib.pyplot as plot

For accessibility, save the gdat record array as its own object. Then, the values can be plotted.

.. code-block:: python

    r = result.gdats

    for name in r.dtype.names:
        if name != "time":
            plt.plot(r['time'], r[name], label=name)
    plot.xlabel("time")
    plot.ylabel("species (counts)")
    _ = plt.legend(frameon=False)

BNG Model object
================

The :code:`bngmodel` method can be used to create a Python object that represents a BNGL model, which can then be somewhat modified.
