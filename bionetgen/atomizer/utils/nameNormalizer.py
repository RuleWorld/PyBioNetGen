import readBNGXML
import argparse
import yaml


def normalizeMatchingMoleculeNamespace(molecule, moleculeSettings):
    # we have to change the name
    if "newname" in moleculeSettings:
        molecule.name = moleculeSettings["newname"]
    if "components" in moleculeSettings:
        for componentSettings in moleculeSettings["components"]:
            matchingComponents = [
                x for x in molecule.components if x.name == componentSettings["name"]
            ]
            for matchingComponent in matchingComponents:
                if "newname" in componentSettings:
                    matchingComponent.name = componentSettings["newname"]
                for stateSettings in componentSettings["states"]:
                    if stateSettings["name"] in matchingComponent.states:
                        idx = matchingComponent.states.index(stateSettings["name"])
                        if "newname" in stateSettings:
                            matchingComponent.states[idx] = stateSettings["newname"]
                            if matchingComponent.activeState == stateSettings["name"]:
                                matchingComponent.activeState = stateSettings["newname"]


def normalizeMoleculeNamespace(molecule, moleculeSettings):
    # molecule name matches
    if molecule.name == moleculeSettings["name"]:
        normalizeMatchingMoleculeNamespace(molecule, moleculeSettings)
    for component in molecule.components:
        if component.name == moleculeSettings["name"].lower():
            if "newname" in moleculeSettings:
                component.name = moleculeSettings["newname"].lower()


def normalizeNamespace(bnglNamespace, normalizationSettings):
    """Changes the namespace of a bngl file

    Keyword arguments:
    bnglNamespace -- The current molecule, rule etc structures
    normalizationSettings -- A dictionary containing those structures whose name we will change
    """

    # change molecule namespace
    for moleculeSettings in normalizationSettings["molecules"]:
        for molecule in bnglNamespace["molecules"]:
            normalizeMoleculeNamespace(molecule, moleculeSettings)

    # change seed species namespace
    for seedspecies in bnglNamespace["seedspecies"]:
        for molecule in seedspecies["structure"].molecules:
            for moleculeSettings in normalizationSettings["molecules"]:
                normalizeMoleculeNamespace(molecule, moleculeSettings)

    # change observable namespace
    for observables in bnglNamespace["observables"]:
        for pattern in observables[2]:
            for molecule in pattern.molecules:
                for moleculeSettings in normalizationSettings["molecules"]:
                    normalizeMoleculeNamespace(molecule, moleculeSettings)

    # change rule namespace
    for ruleDescription in bnglNamespace["rules"]:
        for reactant in ruleDescription[0].reactants:
            for molecule in reactant.molecules:
                for moleculeSettings in normalizationSettings["molecules"]:
                    normalizeMoleculeNamespace(molecule, moleculeSettings)
        for product in ruleDescription[0].products:
            for molecule in product.molecules:
                for moleculeSettings in normalizationSettings["molecules"]:
                    normalizeMoleculeNamespace(molecule, moleculeSettings)


def defineConsole():
    """
    defines the program console line commands
    """
    parser = argparse.ArgumentParser(description="SBML to BNGL translator")
    parser.add_argument(
        "-n", "--normalize", type=str, help="normalization settings file", required=True
    )
    return parser


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()
    with open(namespace.normalize) as f:
        normalizationSettings = yaml.load(f)

    for model in normalizationSettings["model"]:
        bnglNamespace = readBNGXML.parseFullXML(model["name"])

        normalizeNamespace(bnglNamespace, model)

        bnglString = readBNGXML.createBNGLFromDescription(bnglNamespace)
        with open(model["name"] + "_norm.bngl", "w") as f:
            f.write(bnglString)
