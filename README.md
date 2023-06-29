# A simple CLI for BioNetGen 

[![BNG CLI build status](https://github.com/RuleWorld/PyBioNetGen/workflows/bng-cli-tests/badge.svg)](https://github.com/RuleWorld/PyBioNetGen/actions)
[![Open in Remote - Containers](https://img.shields.io/static/v1?label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/RuleWorld/PyBioNetGen)
[![Documentation Status](https://readthedocs.org/projects/pybionetgen/badge/?version=latest)](https://pybionetgen.readthedocs.io/en/latest/?badge=latest)
[![Downloads](https://static.pepy.tech/badge/bionetgen)](https://pepy.tech/project/bionetgen)

This is a simple CLI and a library for [BioNetGen modelling language](http://bionetgen.org/). PyBioNetGen also includes a heavily updated version of [Atomizer](https://github.com/RuleWorld/atomizer) which allows for conversion of models written in [Systems Biology Markup Language (SBML)](https://synonym.caltech.edu/) into BioNetGen language (BNGL) format. 

Please see the [documentation](https://pybionetgen.readthedocs.io/en/latest/) to learn how to use PyBioNetGen. 

## Installation

You will need both python (3.7 and above) and perl installed. Once both are available you can use the following pip command to install the package

```
$ pip install bionetgen
```

### Features 

PyBioNetGen comes with a command line interface (CLI), based on [cement framework](https://builtoncement.com/), as well as a functional library that can be imported. The CLI can be used to run BNGL models, generate Jupyter notebooks and do rudimentary plotting. 

The library side provides a simple BNGL model runner as well as a model object that can be manipulated and used to get libRoadRunner simulators for the model. 

PyBioNetGen also includes a heavily updated version of [Atomizer](https://github.com/RuleWorld/atomizer) which allows for conversion of SBML models into BNGL format. Atomizer can also be used to automatically try to infer the internal structure of SBML species during the conversion, see [here](https://pybionetgen.readthedocs.io/en/latest/atomizer.html) for more information. Please note that this version of Atomizer is the main supported version and the version distributed with BioNetGen will eventually be deprecated. 

The model object requires a system call to BioNetGen so the initialization can be relatively costly, in case you would like to use it for parallel applications, use the [libRoadRunner](http://libroadrunner.org/) simulator instead, unless you are doing NFSim simulations.

### Usage 

Sample CLI usage

```
$ bionetgen -h # help on every subcommand
$ bionetgen run -h # help on run subcommand
$ bionetgen run -i mymodel.bngl -o output_folder # this runs the model in output_folder
```

Sample library usage

```
import bionetgen 

ret = bionetgen.run("/path/to/mymodel.bngl", out="/path/to/output/folder")
# out keyword is optional, if not given, 
# generated files will be deleted after running
res = ret.results['mymodel']
# res will be a numpy record array of your gdat results

model = bionetgen.bngmodel("/path/to/mymodel.bngl")
# model will be a python object that contains all model information
print(model.parameters) # this will print only the parameter block in BNGL format
print(model) # this will print the entire BNGL
model.parameters.k = 1 # setting parameter k to 1
with open("new_model.bngl", "w") as f:
    f.write(str(model)) # writes the changed model to new_model file

# this will give you a libRoadRunner instance of the model
librr_sim = model.setup_simulator()
```

You can find more tutorials [here](https://pybionetgen.readthedocs.io/en/latest/tutorials.html).

### Environment Setup

The following demonstrates setting up and working with a development environment:

```
### create a virtualenv for development

$ make virtualenv

$ source env/bin/activate


### run bionetgen cli application

$ bionetgen --help


### run pytest / coverage

$ make test
```

### Docker

Included is a basic `Dockerfile` for building and distributing `BioNetGen CLI`,
and can be built with the included `make` helper:

```
$ make docker

$ docker run -it bionetgen --help
```

### Publishing to PyPI

You can use `make dist` command to make the distribution and push to PyPI with

```
python -m twine upload dist/*
```

You'll need to have a PyPI API token created, see [here](https://packaging.python.org/tutorials/packaging-projects/) for more information. 
