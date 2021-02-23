# A simple CLI for BioNetGen 

[![BNG CLI build status](https://github.com/ASinanSaglam/BNG_cli/workflows/bng-cli-tests/badge.svg)](https://github.com/ASinanSaglam/BNG_cli/actions)

## Installation

Currently this library is in testing so it's in test PyPI and not directly installable via pip from there. Use the following to get the library

```
$ pip install -i https://test.pypi.org/simple bionetgen
```

### Features 

PyBioNetGen comes with a command line interface (CLI) entrypoint as well as a functional library that can be imported. The CLI can be used to run BNGL models, generate Jupyter notebooks and do rudimentary plotting. 

The library side provides a simple BNGL model runner as well as a model object that can be manipulated and used to get libRoadRunner simulators for the model. 

The model object requires a system call to BioNetGen so the initialization can be relatively costly, in case you would like to use it for parallel applications, use the libRR simulator for those. 

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