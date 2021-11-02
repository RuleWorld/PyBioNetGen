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

Atomizer looks up annotation information on various online resources (namely `Pathway Commons <https://www.pathwaycommons.org/>`_, `BioGRID <https://thebiogrid.org/>`_ and `UniProt <https://www.uniprot.org/>`_).
This generally allows for easier atomization, reducing user input required. If you don't have internet connection you can turn this off with the `-p` option

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -p

Generally a complex model will require several options with a bit of user input in JSON format (see below), for example

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -u user_input.json

If the atomizer output is too cluttered you can adjust the output levels with the `-ll` option

.. code-block:: shell

    bionetgen atomize -i mymodel.xml -o mymodel_flat.bngl -a -u user_input.json -ll "ERROR"

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

These tutorials shows how to use Atomization tool to make a BNGL Model from SBML format. We will Use
various curated models from the `biomodels database <https://www.ebi.ac.uk/biomodels/search?domain=biomodels&query=*%3A*+AND+curationstatus%3A%22Manually+curated%22&numResults=10>`_. 
You can download the specific SBML files by clicking on the titles.

`Biomodels database model 48 <https://www.ebi.ac.uk/biomodels/BIOMD0000000048>`_
---------------------------------------------------------------------------------
​
**Atomizing the Model:** Once you download the SBML file of BMD48, you will have an :code:`.xml` 
file in your directory. Use it as the input to the `atomize` subcommand as shown below. To show the 
effect of using the web services we'll also add the `-p` option to not use the web serices at first

.. code-block:: shell

    bionetgen atomize -i BIOMD0000000048.xml -o BMD48.bngl -a -p

you can name the `bngl` output file whatever you want. This will print out information on the atomization
process. If the output is too cluttered you can look at only the major errors using the following command

.. code-block:: shell

    bionetgen atomize -i BIOMD0000000048.xml -o BMD48.bngl -a -p -ll "ERROR"
     
which prints out 

.. code-block:: shell

    ERROR:SCT212:['EGF_EGFR2']:EGF_EGFR2_P:Atomizer needs user information to determine which element is being modified among component species:['EGF', 'EGF', 'EGFR', 'EGFR']:_p
    ERROR:ATO202:['EGF_EGFR2', 'EGF_EGFR2_PLCg_P']:(('EGF', 'EGF'), ('EGF', 'EGFR'), ('EGFR', 'EGFR')):We need information to resolve the bond structure of these complexes . Please choose among the possible binding candidates that had the most observed frequency in the reaction network or provide a new one
    ERROR:ATO202:['EGF_EGFR2_Shc_Grb2_SOS']:(('EGF', 'Grb2'), ('EGF', 'SOS'), ('EGF', 'Shc'), ('EGFR', 'Grb2'), ('EGFR', 'SOS'), ('EGFR', 'Shc')):We need information to resolve the bond structure of these complexes . Please choose among the possible binding candidates that had the most observed frequency in the reaction network or provide a new one
    Structured molecule type ratio: 0.7

the first three "ERROR"s tells us that atomizer needs user input to resolve certain ambiguities 
in the model. Structured molecule type ratio is the ratio of structured species in the `molecule types`
block of the resulting BNGL to the total number of molecule types, to give an idea of how successful
atomizer was at inferring structure of the species in the model. 

Before we give atomizer more user input, let's try removing the `-p` option to see if atomizer can 
resolve these automatically

.. code-block:: shell

    bionetgen atomize -i BIOMD0000000048.xml -o BMD48.bngl -a -ll "ERROR"

which prints out

.. code-block:: shell

    ERROR:SCT212:['EGF_EGFR2']:EGF_EGFR2_P:Atomizer needs user information to determine which element is being modified among component species:['EGF', 'EGF', 'EGFR', 'EGFR']:_p
    ERROR:ATO202:['EGF_EGFR2_PLCg_P']:(('EGF', 'PLCg'), ('EGFR', 'PLCg')):We need information to resolve the bond structure of these complexes . Please choose among the possible binding candidates that had the most observed frequency in the reaction network or provide a new one
    Structured molecule type ratio: 0.875
 
there were multiple instances of "ERROR:MSC02" that warn the user about issues with connections
to the `BioGRID <https://thebiogrid.org/>`_ service which were removed for clarity. Now we only
have two errors left. 

Resolving errors
================

Now let's take a look at the remaining issues one by one

.. code-block:: shell

    ERROR:SCT212:['EGF_EGFR2']:EGF_EGFR2_P:Atomizer needs user information to determine which element is being modified among component species:['EGF', 'EGF', 'EGFR', 'EGFR']:_p

atomizer is having trouble figuring out where the modification `_p` is supposed to go, which is a 
phosphorylation site. We know that EGFR is the molecule that's being phosphorylated so we make a 
JSON file (here we call it `user-input_1.json`)

.. code-block:: json

  {
	"modificationDefinition": {
		"EGF_EGFR2_P": ["EGFR_P", "EGFR", "Epidermal_Growth_Factor", "Epidermal_Growth_Factor"]
	}
  }

and we rerun atomization with the `-u` option using this JSON file we created

.. code-block:: shell

    bionetgen atomize -i BIOMD0000000048.xml -o BMD48.bngl -a -ll "ERROR" -u user-input-1.json

which returns (disregarding connection errors)

.. code-block:: shell
    
    ERROR:ATO202:['EGF_EGFR2_PLCg', 'EGF_EGFR2_PLCg_P']:(('EGFR', 'PLCg'), ('Epidermal_Growth_Factor', 'PLCg')):We need information to resolve the bond structure of these complexes . Please choose among the possible binding candidates that had the most observed frequency in the reaction network or provide a new one

which tells us that atomizer can't resolve where `PLCg` is binding, let's add that to the JSON file

.. code-block:: json

  {
    "binding_interactions": [
        ["EGFR", "PLCg"]
    ],
	"modificationDefinition": {
		"EGF_EGFR2_P": ["EGFR_P", "EGFR", "Epidermal_Growth_Factor", "Epidermal_Growth_Factor"]
	}
  }

rerunning atomizer should return no errors and you should now have a fully atomized BNGL model.
`Visualizing the model <https://bng-vscode-extension.readthedocs.io/en/latest/usage.html#visualization>`_ 
and using yEd to look at the contact map gives us the following 

.. image:: assets/bmd48.png

`Biomodels database model 19 <https://www.ebi.ac.uk/biomodels/BIOMD0000000019>`_
---------------------------------------------------------------------------------

This model is an expanded version of BioModel 48. Let's follow the same strategy and atomize
it without any input first and see what atomizer says. 

.. code-block:: shell

    bionetgen atomize -i BIOMD0000000019.xml -o BMD19.bngl -a -ll "ERROR"

this returns

.. code-block:: shell

    ERROR:ATO202:['EGF_EGFRm2_GAP_Grb2_Prot', 'EGF_EGFRm2_GAP_Grb2_Sos_Prot', 
                  'EGF_EGFRm2_GAP_Shcm_Grb2_Prot', 'EGF_EGFRm2_GAP_Grb2_Sos_Ras_GTP_Prot', 
                  'EGF_EGFRm2_GAP_Shcm_Grb2_Sos_Prot', 'EGF_EGFRm2_GAP_Grb2_Sos_Ras_GDP_Prot', 
                  'EGF_EGFRm2_GAP_Shcm_Grb2_Sos_Ras_GTP_Prot', 
                  'EGF_EGFRm2_GAP_Shcm_Grb2_Sos_Ras_GDP_Prot']:
                  (('EGF', 'Prot'), ('EGFR', 'Prot'), ('GAP', 'Prot'), 
                  ('Grb2', 'Prot')):We need information to resolve the bond structure of these 
                  complexes . Please choose among the possible binding candidates that had the 
                  most observed frequency in the reaction network or provide a new one
    Structured molecule type ratio: 0.6363636363636364

which tells us that atomizer is having trouble figuring out which binding interaction to include
for `Prot`. We know that protein binds to EGFR so let's include that in a user input JSON file

.. code-block:: json

    {
    "binding_interactions": [
        ["EGFR", "Prot"]
    ]
    }

and now rerunning the atomization using this user input file

.. code-block:: shell

    bionetgen atomize -i BIOMD0000000019.xml -o BMD19.bngl -a -ll "ERROR" -u user-input-1.json

now returns no errors. However, looking at the resuling BNGL shows `Ras_GTP(Ras_GDP~0~1,egfr,i~0~I,m~0~M,raf)`
and we know that Ras should be the base species. We can include that using the `modificationDefinition`
section in the user input file

.. code-block:: json

    {
    "binding_interactions": [
        ["EGFR", "Prot"]
    ],
    "modificationDefinition": {
        "Ras": [],
        "Ras_GTP": ["Ras"],
        "Ras_GDP": ["Ras"]
      }
    }

rerunning atomization using this user input gives a fully atomized BNGL file. 
`Visualizing the model <https://bng-vscode-extension.readthedocs.io/en/latest/usage.html#visualization>`_ 
and using yEd to look at the contact map gives us the following 

.. image:: assets/bmd19.png