.. _atomizer:

########
Atomizer
########

Atomizer is a translator tool that can convert SBML models to BNGL models. Moreover, atomizer is 
capable of extracting implicit information found in SBML models using lexical analysis, reaction
stoichiometry and annotation information. Using this information, atomizer converts SBML species
to structured BNGL complexes. 

This in turn allows for easier identification of modification sites,
binding interactions while making the model easier to understand and analyze. Combined with BNGL 
visualization capabilities, atomizer also allows for easier model comparison of the same biological 
process. 

Getting Started
===============

Make sure you have PyBioNetGen properly installed by running

.. code-block:: shell

    bionetgen -h

If this command doesn't print out help information, install PyBioNetGen with

.. code-block:: shell

    pip install bionetgen

Basics of atomizing a model
===========================

Use the :code:`atomize` method to convert a SBML model to BNGL directly (flat translation)

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl

Using the `-a` option allows for atomization of the model (atomized translation)

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a

if the atomization is taking a long time, try the `-mr` option (please note that this might use up a lot of memory)

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -mr

If you encounter atomization errors, you can fix it by using a user input JSON file which is given by the `-u` option (see below)

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -u user_input.json

Atomizer can look up annotation information on various online resources (namely `Pathway Commons <https://www.pathwaycommons.org/>`_, `BioGRID <https://thebiogrid.org/>`_ and `UniProt <https://www.uniprot.org/>`_).
This generally allows for easier atomization, reducing user input required, given that the annotation information in the SBML file is correct. You can enable this with the `-p` option

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -p

Generally a complex model will require several options with a bit of user input in JSON format (see below), for example

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -p -u user_input.json

If the atomizer output is too cluttered you can adjust the output levels with the `-ll` option

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -p -u user_input.json -ll "ERROR"

we suggest using "ERROR" or "WARNING" for `-ll` argument. 

User input format
=================

The user input JSON file has 4 potential fields. Empty fields can be omitted. 

.. code-block:: json
    
    {
        "reactionDefinition" : [
        ],
        "partialComplexDefinition" : [
        ],
        "binding_interactions" : [
            ["Partner1", "Partner2"]
        ],
        "modificationDefinition": {
            "complex":["molecule1", "molecule2"],
        }
    }

"binding_interactions" field is an array where each element is also an array of two items. 
Both items should be the names of species in the model, exactly as written in the SBML. This represents
that there is a binding interaction between the two items which in turn tells atomizer that there 
should be a binding component on both molecules for each other. 

"modificationDefinition" field is a dictionary where the key is a complex in the model and the value
is an array that reflects what the complex is comprised of. 

"reactionDefinition" field is... 

"partialComplexDefinition" field is...


Examples of atomization
=======================

`Biomodels database model 48 <https://www.ebi.ac.uk/biomodels/BIOMD0000000048>`_
---------------------------------------------------------------------------------

`Biomodels database model 151 <https://www.ebi.ac.uk/biomodels/BIOMD0000000151>`_
---------------------------------------------------------------------------------

`Biomodels database model 543 <https://www.ebi.ac.uk/biomodels/BIOMD0000000543>`_
---------------------------------------------------------------------------------