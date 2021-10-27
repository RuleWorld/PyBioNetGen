# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 21:06:43 2013

@author: proto
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Dec  6 17:42:31 2011

@author: proto
"""
from copy import deepcopy, copy
from . import analyzeSBML
import bionetgen.atomizer.utils.structures as st
from bionetgen.atomizer.utils.util import logMess
import re

# import biogrid
import marshal
import functools
import bionetgen.atomizer.utils.pathwaycommons as pwcm
from collections import Counter, defaultdict
import itertools
from .atomizerUtils import BindingException
from . import resolveSCT
from . import atomizationAux as atoAux


def isInComplexWith(moleculeSet, parser=None):
    """
    given a list of binding candidates, it gets the uniprot ID from annotation and queries
    the pathway commons class to see if there's known binding information for those two
    """
    validPairs = []
    for element in moleculeSet:
        # if element[0] == element[1]:
        #    return []

        name1 = atoAux.getURIFromSBML(element[0], parser, ["uniprot", "go"])
        name2 = atoAux.getURIFromSBML(element[1], parser, ["uniprot", "go"])

        modelAnnotation = parser.extractModelAnnotation()
        modelOrganism = (
            modelAnnotation["BQB_OCCURS_IN"]
            if "BQB_OCCURS_IN" in modelAnnotation
            else None
        )
        molecule1 = name1[0].split("/")[-1] if name1 else element[0]
        molecule2 = name2[0].split("/")[-1] if name2 else element[1]

        simpleOrganism = (
            [x.split("/")[-1] for x in modelOrganism] if modelOrganism else None
        )

        bindingResults = pwcm.queryBioGridByName(
            molecule1, molecule2, simpleOrganism, element[0], element[1]
        )
        if not bindingResults:
            bindingResults = pwcm.queryBioGridByName(
                element[0], element[1], None, None, None
            )
        # bindingResults = None
        # bindingResults = pwcm.isInComplexWith([element[0], name1], [element[1], name2], organism=modelOrganism)
        if bindingResults:
            validPairs.append(element)
    # use pathway commosn as fallback since its much slower
    # it is stupid slow. Enable it as a not on default option
    if not validPairs:
        for element in moleculeSet:
            # if element[0] == element[1]:
            #    return []

            name1 = atoAux.getURIFromSBML(element[0], parser, ["uniprot", "go"])
            name2 = atoAux.getURIFromSBML(element[1], parser, ["uniprot", "go"])
            modelAnnotation = parser.extractModelAnnotation()
            modelOrganism = (
                modelAnnotation["BQB_OCCURS_IN"]
                if "BQB_OCCURS_IN" in modelAnnotation
                else None
            )
            bindingResults = pwcm.isInComplexWith(
                [element[0], name1], [element[1], name2], organism=modelOrganism
            )
            if bindingResults:
                validPairs.append(element)
    return validPairs


def identifyReaction(equivalenceDictionary, originalElement, modifiedElement):
    for classification in equivalenceDictionary:
        if set([originalElement, modifiedElement]) in [
            set(x) for x in equivalenceDictionary[classification]
        ]:
            return classification
    return None


def createEmptySpecies(name):
    species = st.Species()
    molecule = st.Molecule(name)
    species.addMolecule(molecule)
    return species


def addStateToComponent(species, moleculeName, componentName, state):
    for molecule in species.molecules:
        if moleculeName == molecule.name:
            for component in molecule.components:
                if componentName == component.name:
                    tmp = component.activeState
                    if state not in component.states:
                        component.addState(state)
                    elif state in component.states:
                        component.setActiveState(state)
                    return tmp


def addComponentToMolecule(species, moleculeName, componentName):
    for molecule in species.molecules:
        if moleculeName == molecule.name:
            if componentName not in [x.name for x in molecule.components]:
                component = st.Component(componentName)
                molecule.addComponent(component)
                return True
    return False


def addBondToComponent(species, moleculeName, componentName, bond, priority=1):
    order = 1
    for molecule in species.molecules:
        if moleculeName == molecule.name:
            if (
                priority == order
                or len([x for x in species.molecules if x.name == moleculeName])
                == order
            ):
                for component in molecule.components:
                    if componentName == component.name:
                        # if we are adding a second bond to the same component
                        # it actually means that we have two components with the
                        # same name
                        if len(component.bonds) == 0:
                            component.addBond(bond)
                            return
                        else:
                            newComponent = st.Component(componentName)
                            newComponent.addBond(bond)
                            molecule.addComponent(newComponent)
                            return
            else:
                order += 1


def solveComplexBinding(totalComplex, pathwaycommonsFlag, parser, compositionEntry):
    """
    given two binding complexes it will attempt to find the ways in which they bind using different criteria

    """

    def sortMolecules(array, reverse):
        return sorted(
            array,
            key=lambda molecule: (
                len(molecule.components),
                len([x for x in molecule.components if x.activeState not in [0, "0"]]),
                len(str(molecule)),
                str(molecule),
            ),
            reverse=reverse,
        )

    def getBiggestMolecule(array):
        sortedMolecule = sortMolecules(array, reverse=False)

        # sortedMolecule = sorted(sortedMolecule, key=lambda rule: len(rule.components))

        return sortedMolecule[-1]

    def getNamedMolecule(array, name):

        for molecule in sortMolecules(array, True):
            if molecule.name == name:
                return molecule
            elif molecule.trueName == name:
                return molecule

    names1 = [str(x.trueName) for x in totalComplex[0]]
    names2 = [str(x.trueName) for x in totalComplex[1]]
    bioGridDict = {}
    # find all pairs of molecules
    comb = set([tuple(sorted([x, y])) for x in names1 for y in names2])
    comb2 = set(
        [tuple(sorted([x, y])) for x in compositionEntry for y in compositionEntry]
    )

    dbPair = set([])
    combTemp = set()

    # search pathway commons for binding candidates
    if pathwaycommonsFlag:
        dbPair = isInComplexWith(comb, parser)
    else:
        for element in comb:
            if (
                element[0].upper() in bioGridDict
                and element[1] in bioGridDict[element[0].upper()]
                or element[1].upper() in bioGridDict
                and element[0] in bioGridDict[element[1].upper()]
            ):
                # logMess('INFO:ATO001', 'Biogrid info: {0}:{1}'.format(element[0], element[1]))
                dbPair.add((element[0], element[1]))
        # elif pathwaycommonsFlag:
        #    if pwcm.isInComplexWith(element[0], element[1]):
        #        dbPair.add((element[0], element[1]))
    dbPair = list(dbPair)

    if dbPair != []:
        mol1 = mol2 = None
        # select the best candidate if there's many ways to bind (in general
        # one that doesn't overlap with an already exising pair)
        finalDBpair = []
        if len(dbPair) > 1:

            for element in dbPair:
                mset1 = Counter(element)
                mset2 = Counter(names1)
                mset3 = Counter(names2)
                intersection1 = mset1 & mset2
                intersection2 = mset1 & mset3
                intersection1 = list(intersection1.elements())
                intersection2 = list(intersection2.elements())
                if len(intersection1) < 2 and len(intersection2) < 2:
                    finalDBpair.append(element)
        if len(finalDBpair) > 0:
            dbPair = finalDBpair

        if len(dbPair) > 1:

            # @FIXME: getNamedMolecule should never receive parameters that cause it to return null, but somehow that's what is happening
            # when you receive a malformed user definition file. The error
            # should be caught way before we reach this point
            tmpComplexSubset1 = [
                getNamedMolecule(totalComplex[0], element[0])
                for element in dbPair
                if getNamedMolecule(totalComplex[0], element[0]) is not None
            ]
            if not tmpComplexSubset1:
                tmpComplexSubset1 = [
                    getNamedMolecule(totalComplex[0], element[1])
                    for element in dbPair
                    if getNamedMolecule(totalComplex[0], element[1]) is not None
                ]
                tmpComplexSubset2 = [
                    getNamedMolecule(totalComplex[1], element[0])
                    for element in dbPair
                    if getNamedMolecule(totalComplex[1], element[0]) is not None
                ]
            else:
                tmpComplexSubset2 = [
                    getNamedMolecule(totalComplex[1], element[1])
                    for element in dbPair
                    if getNamedMolecule(totalComplex[1], element[1]) is not None
                ]

            mol1 = getBiggestMolecule(tmpComplexSubset1)
            mol2 = getBiggestMolecule(tmpComplexSubset2)
            # was ATO002
            logMess(
                "WARNING:ATO111",
                "{0}-{1}:The two pairs can bind in these ways according to BioGrid/Pathwaycommons:{2}:Defaulting to:('{3}', '{4}')".format(
                    names1, names2, dbPair, mol1.name, mol2.name
                ),
            )

        else:
            mol1 = getNamedMolecule(totalComplex[0], dbPair[0][0])
            if not mol1:
                mol1 = getNamedMolecule(totalComplex[1], dbPair[0][0])
                mol2 = getNamedMolecule(totalComplex[0], dbPair[0][1])

            else:
                mol2 = getNamedMolecule(totalComplex[1], dbPair[0][1])
                if not mol2:
                    mol1 = getNamedMolecule(totalComplex[1], dbPair[0][0])
                    mol2 = getNamedMolecule(totalComplex[0], dbPair[0][1])

            logMess(
                "INFO:ATO001",
                "Binding information found in BioGrid/Pathwaycommons for for {0}-{1}".format(
                    mol1.name, mol2.name
                ),
            )

    else:

        # mol1 = getBiggestMolecule(totalComplex[0])
        # mol2 = getBiggestMolecule(totalComplex[1])
        """
        if pathwaycommonsFlag:
            logMess('ERROR:ATO201', "We don't know how {0} and {1} bind together and there's no relevant BioGrid/Pathway commons information. Not atomizing".format(
                [x.name for x in totalComplex[0]], [x.name for x in totalComplex[1]]))
            # addAssumptions('unknownBond',(mol1.name,mol2.name))
        else:

            logMess('ERROR:ATO202', "We don't know how {0} and {1} bind together. Not atomizing".format(
                [x.name for x in totalComplex[0]], [x.name for x in totalComplex[1]]))
            # addAssumptions('unknownBond',(mol1.name,mol2.name))
        """
        raise BindingException(
            "{0}-{1}".format(
                sorted([x.name for x in totalComplex[0]]),
                sorted([x.name for x in totalComplex[1]]),
            ),
            comb,
        )

    return mol1, mol2


def getComplexationComponents2(
    moleculeName,
    species,
    bioGridFlag,
    pathwaycommonsFlag=False,
    parser=None,
    bondSeeding=[],
    bondExclusion=[],
    database=None,
):
    """
    method used during the atomization process. It determines how molecules
    in a species bind together
    """

    def sortMolecules(array, reverse):
        return sorted(
            array,
            key=lambda molecule: (
                len(molecule.components),
                len([x for x in molecule.components if x.activeState not in [0, "0"]]),
                len(str(molecule)),
                str(molecule),
            ),
            reverse=reverse,
        )

    def getBiggestMolecule(array):
        sortedMolecule = sortMolecules(array, reverse=False)

        # sortedMolecule = sorted(sortedMolecule, key=lambda rule: len(rule.components))

        return sortedMolecule[-1]

    def getNamedMolecule(array, name):

        for molecule in sortMolecules(array, True):
            if molecule.name == name:
                return molecule

    speciesDict = {}
    # this array will contain all molecules that bind together
    pairedMolecules = []
    for x in sortMolecules(species.molecules, reverse=True):
        for y in x.components:
            if y.name not in speciesDict:
                speciesDict[y.name] = []
            speciesDict[y.name].append(x)
    # this array wil contain all molecules that dont bind to anything
    orphanedMolecules = [x for x in species.molecules]
    # seed the list of pairs from the seeds
    pairedMolecules = copy(bondSeeding)
    if bondSeeding:
        orphanedMolecules = [
            x for x in orphanedMolecules for y in bondSeeding if x not in y
        ]

    # determine how molecules bind together
    redundantBonds = []

    for x in sortMolecules(species.molecules, reverse=True):
        for component in [
            y for y in x.components if y.name.lower() in list(speciesDict.keys())
        ]:
            if x.name.lower() in speciesDict:
                if (x in speciesDict[component.name.lower()]) and component.name in [
                    y.name.lower() for y in speciesDict[x.name.lower()]
                ]:
                    for mol in speciesDict[x.name.lower()]:
                        if (
                            mol.name.lower() == component.name
                            and x != mol
                            and x in speciesDict[component.name]
                        ):
                            speciesDict[x.name.lower()].remove(mol)
                            speciesDict[component.name].remove(x)
                            if (
                                x not in orphanedMolecules
                                and mol not in orphanedMolecules
                            ):
                                # FIXME: is it necessary to remove double bonds
                                # in complexes?

                                lhs = set([])
                                rhs = set([])
                                repeatedFlag = False
                                for pair in pairedMolecules:

                                    if x in pair:
                                        lhs.add(pair[0])
                                        lhs.add(pair[1])
                                    elif mol in pair:
                                        rhs.add(pair[0])
                                        rhs.add(pair[1])
                                    # is this particular pair of molecules bound together?
                                    if x in pair and mol in pair:
                                        repeatedFlag = True
                                        break
                                # this pair already exists
                                if repeatedFlag:
                                    continue
                                redundantBonds.append([x, mol])
                                intersection = lhs.intersection(rhs)
                                redundantBonds[-1].extend(list(intersection))
                                if len(redundantBonds[-1]) < 3:
                                    redundantBonds.pop()
                                # continue
                            if (
                                [x, mol] not in bondSeeding
                                and [mol, x] not in bondSeeding
                                and [x, mol] not in bondExclusion
                                and [mol, x] not in bondExclusion
                            ):
                                pairedMolecules.append([x, mol])
                            if x in orphanedMolecules:
                                orphanedMolecules.remove(x)
                            if mol in orphanedMolecules:
                                orphanedMolecules.remove(mol)

    if len(redundantBonds) > 0:
        for x in redundantBonds:
            if database:
                atoAux.addAssumptions(
                    "redundantBonds",
                    tuple(sorted([y.name for y in x])),
                    database.assumptions,
                )
                atoAux.addAssumptions(
                    "redundantBondsMolecules",
                    (tuple(sorted([y.name for y in x])), moleculeName),
                    database.assumptions,
                )
            logMess(
                "WARNING:CTX001",
                "Redundant bonds detected between molecules {0} in species {1}".format(
                    [y.name for y in x], moleculeName
                ),
            )
    totalComplex = [set(x) for x in pairedMolecules]
    isContinuousFlag = True

    # iterate over orphaned and find unidirectional interactions
    # e.g. if a molecule has a previous known interaction with the
    # same kind of molecule, even if it has no available components
    # e.g. k-mers`

    for element in speciesDict:
        for individualMolecule in speciesDict[element]:
            if individualMolecule in orphanedMolecules:
                candidatePartner = [
                    x
                    for x in species.molecules
                    if x.name.lower() == element and x != individualMolecule
                ]
                if len(candidatePartner) == 1:
                    pairedMolecules.append([candidatePartner[0], individualMolecule])
                    orphanedMolecules.remove(individualMolecule)
    # determine which pairs form a continuous chain

    while isContinuousFlag:
        isContinuousFlag = False
        for idx in range(0, len(totalComplex) - 1):
            for idx2 in range(idx + 1, len(totalComplex)):
                if len([x for x in totalComplex[idx] if x in totalComplex[idx2]]) > 0:
                    totalComplex[idx] = totalComplex[idx].union(totalComplex[idx2])
                    totalComplex.pop(idx2)
                    isContinuousFlag = True
                    break
            if isContinuousFlag:
                break
    # now we process those molecules where we need to create a new component
    for element in orphanedMolecules:

        for mol1 in species.molecules:
            # when adding orphaned molecules make sure it's not already in
            # the list
            if mol1 == element and mol1 not in set().union(*totalComplex):
                totalComplex.append(set([mol1]))
    # now we process for those molecules we are not sure how do they bind
    while len(totalComplex) > 1:

        if len(totalComplex[0]) == 1 and len(totalComplex[1]) == 1:
            mol1 = list(totalComplex[0])[0]
            mol2 = list(totalComplex[1])[0]
        else:
            mol1, mol2 = solveComplexBinding(
                totalComplex,
                pathwaycommonsFlag,
                parser,
                database.prunnedDependencyGraph[moleculeName][0],
            )
        pairedMolecules.append([mol1, mol2])
        totalComplex[0] = totalComplex[0].union(totalComplex[1])
        totalComplex.pop(1)
    # totalComplex.extend(orphanedMolecules)
    return pairedMolecules


def getTrueTag(dependencyGraph, molecule):
    """
    given any modified or basic element it returns its basic
    name
    """
    if dependencyGraph[molecule] == []:
        return molecule
    elif dependencyGraph[molecule][0][0] == molecule:
        return molecule
    else:
        return getTrueTag(dependencyGraph, dependencyGraph[molecule][0][0])


def createCatalysisRBM(
    dependencyGraph,
    element,
    translator,
    reactionProperties,
    equivalenceDictionary,
    sbmlAnalyzer,
    database,
):
    """
    if it's a catalysis reaction create a new component/state
    """
    if dependencyGraph[element[0]][0][0] == element[0]:
        if element[0] not in translator:
            translator[element[0]] = createEmptySpecies(element[0])
    else:
        componentStateArray = []
        tmp = element[0]
        existingComponents = []
        memory = []
        forceActivationSwitch = False
        while dependencyGraph[tmp] != []:
            # what kind of catalysis are we dealing with
            # classification = identifyReaction(
            #                                  equivalenceDictionary,
            #                                  dependencyGraph[tmp][0][0],tmp)

            classifications = None
            if not classifications:
                classifications = identifyReaction(
                    equivalenceDictionary, dependencyGraph[tmp][0][0], tmp
                )
                classifications = (
                    classifications if classifications in reactionProperties else None
                )
                if classifications is not None:
                    classifications = [classifications]
            if not classifications:
                classifications = sbmlAnalyzer.findMatchingModification(
                    tmp, dependencyGraph[tmp][0][0]
                )

            if not classifications:
                classifications = sbmlAnalyzer.findMatchingModification(
                    element[0], dependencyGraph[tmp][0][0]
                )

            # if we know what classification it is then add the corresponding
            # components and states
            if classifications is not None:
                for classification in classifications:
                    componentStateArray.append(reactionProperties[classification])
                    # classificationArray.append([classification,
                    #                            tmp,dependencyGraph[tmp]
                    #                            [0][0]])
                    existingComponents.append(reactionProperties[classification][0])
            # if we don't know we can create a force 1:1 modification
            elif (
                database.forceModificationFlag
                and classifications is None
                and not forceActivationSwitch
            ):
                forceActivationSwitch = True
                baseName = getTrueTag(
                    dependencyGraph, dependencyGraph[element[0]][0][0]
                )

                species = createEmptySpecies(baseName)

                componentStateArray.append(["{0}".format(tmp), tmp])
                if not (
                    element[0] in database.userLabelDictionary
                    and database.userLabelDictionary[element[0]][0][0] == baseName
                ):
                    logMess(
                        "WARNING:LAE002",
                        "adding forced transformation: {0}:{1}:{2}".format(
                            baseName, dependencyGraph[element[0]][0][0], element[0]
                        ),
                    )
                # return
            # bail out if we couldn't figure out what modification it is
            elif classifications is None:
                logMess(
                    "DEBUG:MSC001",
                    "unregistered modification: {0}:{1}".format(
                        element[0], dependencyGraph[element[0]]
                    ),
                )
            memory.append(tmp)
            tmp = dependencyGraph[tmp][0][0]
            if tmp in memory:
                raise atoAux.CycleError(memory)
        baseName = getTrueTag(dependencyGraph, dependencyGraph[element[0]][0][0])

        species = createEmptySpecies(baseName)
        # use the already existing structure if its in the
        # translator,otherwise empty
        if baseName in translator:
            species = translator[baseName]
        # modifiedSpecies = deepcopy(translator[dependencyGraph[element[0]][0][0]])

        # modified species needs to start from the base speceis sine componentStateArray should contain the full set of modifications
        # check that this works correctly for double modifications
        modifiedSpecies = deepcopy(translator[baseName])
        # this counter is here for multi level modification events (e.g. double
        # phosporylation)
        modificationCounter = {
            componentState[0]: 2 for componentState in componentStateArray
        }
        for componentState in componentStateArray:
            addComponentToMolecule(species, baseName, componentState[0])
            addComponentToMolecule(modifiedSpecies, baseName, componentState[0])
            tmp = addStateToComponent(
                species, baseName, componentState[0], componentState[1]
            )
            if tmp == componentState[1]:
                addStateToComponent(
                    species,
                    baseName,
                    componentState[0],
                    componentState[1] + componentState[1],
                )
            # this modification was already activated so create a second
            # modification component
            if (
                addStateToComponent(
                    modifiedSpecies, baseName, componentState[0], componentState[1]
                )
                == componentState[1]
            ):
                componentName = "{0}{1}".format(
                    componentState[0], modificationCounter[componentState[0]]
                )
                modificationCounter[componentState[0]] += 1
                addComponentToMolecule(modifiedSpecies, baseName, componentName)
                addStateToComponent(
                    modifiedSpecies, baseName, componentName, componentState[1]
                )
            addStateToComponent(species, baseName, componentState[0], "0")
        # update the base species
        if len(componentStateArray) > 0:
            translator[baseName] = deepcopy(species)
            translator[element[0]] = modifiedSpecies


globalNumberGenerator = []


def getBondNumber(molecule1, molecule2):
    """
    keeps a model-level registry of of all the molecule pairs and returns a unique index
    """
    moleculeList = tuple(sorted([molecule1, molecule2]))
    if moleculeList not in globalNumberGenerator:
        globalNumberGenerator.append(moleculeList)

    return globalNumberGenerator.index(moleculeList)


def createBindingRBM(
    element,
    translator,
    dependencyGraph,
    bioGridFlag,
    pathwaycommonsFlag,
    parser,
    database,
):
    species = st.Species()

    # go over the sct and reuse existing stuff

    for molecule in dependencyGraph[element[0]][0]:
        if molecule in translator:
            tmpSpecies = translator[molecule]
            if molecule != getTrueTag(dependencyGraph, molecule):
                original = translator[getTrueTag(dependencyGraph, molecule)]
                updateSpecies(tmpSpecies, original.molecules[0])
            if tmpSpecies.molecules[0].name in database.constructedSpecies:
                tmpSpecies.molecules[0].trueName = molecule
            else:
                tmpSpecies.molecules[0].trueName = tmpSpecies.molecules[0].name
            species.addMolecule(deepcopy(tmpSpecies.molecules[0]))
        else:
            mol = st.Molecule(molecule)
            mol.trueName = molecule
            # dependencyGraph[molecule] = deepcopy(mol)
            species.addMolecule(mol)
    dependencyGraphCounter = Counter(dependencyGraph[element[0]][0])

    # XXX: this wont work for species with more than one molecule with the
    # same name
    changeFlag = False
    partialBonds = defaultdict(list)
    for partialUserEntry in database.partialUserLabelDictionary:
        partialCounter = Counter(partialUserEntry)
        if all(
            [partialCounter[x] <= dependencyGraphCounter[x] for x in partialCounter]
        ):
            changeFlag = True
            for molecule in database.partialUserLabelDictionary[
                partialUserEntry
            ].molecules:
                for molecule2 in species.molecules:
                    if molecule.name == molecule2.name:
                        for component in molecule.components:
                            for bond in component.bonds:
                                if molecule2.name not in [
                                    x.name for x in partialBonds[bond]
                                ]:
                                    partialBonds[bond].append(molecule2)
                        """
                        for component in molecule.components:
                            component2 = [x for x in molecule2.components if x.name == component.name]
                            # component already exists in species template
                            if component2:
                                if component.bonds:
                                    component2[0].bonds = component.bonds
                            else:
                                molecule2.addComponent(deepcopy(component))
                        """

    bondSeeding = [partialBonds[x] for x in partialBonds if x > 0]
    bondExclusion = [partialBonds[x] for x in partialBonds if x < 0]
    # how do things bind together?
    moleculePairsList = getComplexationComponents2(
        element[0],
        species,
        bioGridFlag,
        pathwaycommonsFlag,
        parser,
        bondSeeding,
        bondExclusion,
        database,
    )

    # moleculeCount = Counter([y for x in moleculePairsList for y in x])
    # print moleculeCount
    # moleculePairsList = [sorted(x) for x in moleculePairsList]
    # moleculePairsList.sort(key=lambda x: [-moleculeCount[x[0]],(str(x[0]), x[0],str(x[1]),x[1])])
    # TODO: update basic molecules with new components
    # translator[molecule[0].name].molecules[0].components.append(deepcopy(newComponent1))
    # translator[molecule[1].name].molecules[0].components.append(deepcopy(newComponent2))
    moleculeCounter = defaultdict(list)
    for molecule in moleculePairsList:
        flag = False

        # create an index on m0 and m1 depending on their name and repeats in
        # the species
        if molecule[0] not in moleculeCounter[molecule[0].name]:
            moleculeCounter[molecule[0].name].append(molecule[0])
        if molecule[1] not in moleculeCounter[molecule[1].name]:
            moleculeCounter[molecule[1].name].append(molecule[1])
        m0index = moleculeCounter[molecule[0].name].index(molecule[0])
        m1index = moleculeCounter[molecule[1].name].index(molecule[1])
        bondIdx = getBondNumber(
            "{0}{1}".format(molecule[0].name, m0index),
            "{0}{1}".format(molecule[1].name, m1index),
        )
        # add bonds where binding components already exist and they are not
        # occupied
        for component in molecule[0].components:
            if component.name == molecule[1].name.lower() and len(component.bonds) == 0:
                component.bonds.append(bondIdx)
                flag = True
                break
        if not flag:
            # create components if they dont exist already.
            # Add a bond afterwards
            newComponent1 = st.Component(molecule[1].name.lower())

            molecule[0].components.append(newComponent1)

            try:
                if newComponent1.name not in [
                    x.name for x in translator[molecule[0].name].molecules[0].components
                ]:
                    translator[molecule[0].name].molecules[0].components.append(
                        deepcopy(newComponent1)
                    )
            except KeyError as e:
                print(
                    "The translator doesn't know the molecule: {}".format(
                        molecule[0].name
                    )
                )
                raise e
            molecule[0].components[-1].bonds.append(bondIdx)
        flag = False
        # same thing for the other member of the bond
        for component in molecule[1].components:
            if component.name == molecule[0].name.lower() and len(component.bonds) == 0:
                component.bonds.append(bondIdx)
                flag = True
                break
        if not flag:
            newComponent2 = st.Component(molecule[0].name.lower())
            molecule[1].components.append(newComponent2)
            if molecule[0].name != molecule[1].name:
                if newComponent2.name not in [
                    x.name for x in translator[molecule[1].name].molecules[0].components
                ]:
                    translator[molecule[1].name].molecules[0].components.append(
                        deepcopy(newComponent2)
                    )
            molecule[1].components[-1].bonds.append(bondIdx)

    # update the translator
    translator[element[0]] = species


def atomize(
    dependencyGraph,
    weights,
    translator,
    reactionProperties,
    equivalenceDictionary,
    bioGridFlag,
    sbmlAnalyzer,
    database,
    parser,
):
    """
    The atomizer's main methods. Receives a dependency graph
    """
    redrawflag = True
    loops = 0
    while redrawflag and loops < 10:
        loops += 1
        bindingCounter = Counter()
        bindingFailureDict = {}

        for idx, element in enumerate(weights):
            # unnamed molecule?
            if len(element[0]) == 0:
                continue
            # 0 molecule
            if element[0] == "0":
                continue
            # user defined molecules to be the zero molecule
            if dependencyGraph[element[0]] == [["0"]]:
                zeroSpecies = st.Species()
                zeroMolecule = st.Molecule("0")
                zeroSpecies.addMolecule(zeroMolecule)
                translator[element[0]] = zeroSpecies
                continue
            # undivisible molecules

            elif dependencyGraph[element[0]] == []:
                if element[0] not in translator:
                    translator[element[0]] = createEmptySpecies(element[0])
            else:
                if len(dependencyGraph[element[0]][0]) == 1:
                    # catalysis
                    createCatalysisRBM(
                        dependencyGraph,
                        element,
                        translator,
                        reactionProperties,
                        equivalenceDictionary,
                        sbmlAnalyzer,
                        database,
                    )
                else:
                    try:
                        createBindingRBM(
                            element,
                            translator,
                            dependencyGraph,
                            bioGridFlag,
                            database.pathwaycommons,
                            parser,
                            database,
                        )

                    except BindingException as e:
                        for c in e.combinations:
                            bindingCounter[c] += 1
                            bindingFailureDict[element[0]] = e.combinations
                        logMess(
                            "DEBUG:ATO003",
                            "We don't know how {0} binds together in complex {1}. Not atomizing".format(
                                e.value, element[0]
                            ),
                        )

                        # there awas an issue during binding, don't atomize
                        translator[element[0]] = createEmptySpecies(element[0])

        # evaluate species that weren't bound properly and see if we can get information from all over the model to find the right binding partner
        bindingTroubleLog = defaultdict(list)
        modifiedPairs = set()

        redrawflag = False
        for molecule in bindingFailureDict:
            bindingWinner = defaultdict(list)
            for candidateTuple in bindingFailureDict[molecule]:
                bindingWinner[bindingCounter[candidateTuple]].append(candidateTuple)
            bestBindingCandidates = bindingWinner[max(bindingWinner.keys())]
            if len(bestBindingCandidates) > 1:
                bindingTroubleLog[tuple(sorted(bestBindingCandidates))].append(molecule)
            else:
                bindingPair = bestBindingCandidates[0]
                if bindingPair not in modifiedPairs:
                    modifiedPairs.add(bindingPair)
                else:
                    continue
                c1 = st.Component(bindingPair[1].lower())
                c2 = st.Component(bindingPair[0].lower())
                molecule1 = translator[
                    translator[bindingPair[0]].molecules[0].name
                ].molecules[0]
                molecule2 = translator[
                    translator[bindingPair[1]].molecules[0].name
                ].molecules[0]

                molecule1.addComponent(c1)
                molecule2.addComponent(c2)
                redrawflag = True
                logMess(
                    "INFO:ATO031",
                    "Determining that {0} binds together based on frequency of the bond in the reaction network.".format(
                        bindingPair
                    ),
                )
    for trouble in bindingTroubleLog:
        logMess(
            "ERROR:ATO202",
            "{0}:{1}:We need information to resolve the bond structure of these complexes . \
Please choose among the possible binding candidates that had the most observed frequency in the reaction network or provide a new one".format(
                bindingTroubleLog[trouble], trouble
            ),
        )
    # renaming of components as needed for readability.
    for spname in translator:
        species = translator[spname]
        orig_species_st2 = species.str2()
        for molec in species.molecules:
            for component in molec.components:
                if component.name.startswith("_"):
                    # component starts with "_", adjust
                    component.name = re.sub("^(_)+", "", component.name)
                if component.name.endswith("_"):
                    # component starts with "_", adjust
                    component.name = re.sub("(_)+$", "", component.name)
                numbered_states = False
                for ist, state in enumerate(component.states):
                    orig_state = state
                    if state.startswith("_"):
                        component.states[ist] = re.sub("^(_)+", "", state)
                    if state.endswith("_"):
                        component.states[ist] = re.sub("(_)+$", "", state)
                    if (component.states[ist].lower() in component.name.lower()) and (
                        len(component.states[ist]) > 5
                    ):
                        # the component state is named after component, rename
                        numbered_states = True
                    # ensure active state is updated
                    if orig_state == component.activeState:
                        component.activeState = component.states[ist]
                if numbered_states:
                    ctr = 1
                    for ist, state in enumerate(component.states):
                        orig_state = state
                        if state == "0":
                            continue
                        else:
                            component.states[ist] = str(ctr)
                            ctr += 1
                        # ensure active state is updated
                        if orig_state == component.activeState:
                            component.activeState = component.states[ist]
        # log the info
        new_species_str2 = species.str2()
        if new_species_str2 != orig_species_st2:
            logMess(
                "INFO:ATO032",
                f"Renamed species from {orig_species_st2} to {new_species_str2}",
            )
    # renaming can introduce name clashes of components, we need to renumber them
    # if necessary. First pass for counting
    for spname in translator:
        species = translator[spname]
        orig_species_st2 = species.str2()
        for molec in species.molecules:
            comp_counter = {}
            for component in molec.components:
                # add to counter if we don't have it
                if component.name not in comp_counter:
                    comp_counter[component.name] = -1
                # make sure we have the right count
                else:
                    if comp_counter[component.name] < 0:
                        comp_counter[component.name] = 2
                    else:
                        comp_counter[component.name] += 1
            # remove unnecessary stuff
            to_remove = []
            for comp in comp_counter:
                if comp_counter[comp] < 0:
                    to_remove.append(comp)
            for tr in to_remove:
                comp_counter.pop(tr)
            # rename the components
            comp_counter_2 = {}
            for component in molec.components:
                # check if we have multiple of this component
                if component.name not in comp_counter:
                    continue
                # we do have multiples, check where we are at
                if component.name not in comp_counter_2:
                    # our first encounter
                    comp_counter_2[component.name] = 1
                    component.name += "1"
                else:
                    comp_counter_2[component.name] += 1
                    component.name += f"{comp_counter_2[component.name]}"
        # report
        new_species_str2 = species.str2()
        if new_species_str2 != orig_species_st2:
            logMess(
                "INFO:ATO033",
                f"Renumbered components from {orig_species_st2} to {new_species_str2}",
            )


def updateSpecies(species, referenceMolecule):
    flag = False
    for moleculeStructure in species.molecules:
        if moleculeStructure.name == referenceMolecule.name:
            for component in referenceMolecule.components:
                count = [x.name for x in referenceMolecule.components].count(
                    component.name
                )
                count -= [x.name for x in moleculeStructure.components].count(
                    component.name
                )
                newComponent = st.Component(component.name)
                # if len(component.states) > 0:
                #    newComponent.addState('0')
                if count > 0:
                    for _ in range(0, count):
                        # just make a copy of the reference component and set active state to 0
                        componentCopy = deepcopy(component)
                        componentCopy.setActiveState("0")
                        moleculeStructure.addComponent(componentCopy)
                elif count < 0:
                    for _ in range(0, -count):
                        # FIXME: does not fully copy the states
                        referenceMolecule.addComponent(deepcopy(newComponent))
                        flag = True
                elif count == 0:
                    localComponents = [
                        x
                        for x in moleculeStructure.components
                        if x.name == component.name
                    ]
                    referenceComponents = [
                        x
                        for x in referenceMolecule.components
                        if x.name == component.name
                    ]
                    if [x.states for x in localComponents] != [
                        x.states for x in referenceComponents
                    ]:
                        for lc in localComponents:
                            for rc in referenceComponents:
                                for ls in lc.states:
                                    if ls not in rc.states:
                                        rc.addState(ls, update=False)
                                for rs in rc.states:
                                    if rs not in lc.states:
                                        lc.addState(rs, update=False)

            for component in moleculeStructure.components:
                count = [x.name for x in referenceMolecule.components].count(
                    component.name
                )
                count -= [x.name for x in moleculeStructure.components].count(
                    component.name
                )
                newComponent = st.Component(component.name)
                if len(component.states) > 0:
                    newComponent.addState(component.states[0])
                    newComponent.addState("0")
                if count > 0:
                    for idx in range(0, count):
                        moleculeStructure.addComponent(deepcopy(newComponent))
                elif count < 0:
                    for idx in range(0, -count):
                        referenceMolecule.addComponent(deepcopy(newComponent))
                        flag = True

    return flag


def propagateChanges(translator, dependencyGraph):
    flag = True
    while flag:
        flag = False
        for dependency in dependencyGraph:
            if dependencyGraph[dependency] == []:
                continue
            for molecule in dependencyGraph[dependency][0]:
                try:
                    if updateSpecies(
                        translator[dependency],
                        translator[getTrueTag(dependencyGraph, molecule)].molecules[0],
                    ):
                        flag = True
                except:
                    logMess(
                        "CRITICAL:Program", "Species is not being properly propagated"
                    )
                    flag = False


def sanityCheck(database):
    """
    checks for critical atomization errors like isomorphism
    """
    stringrep = {x: str(database.translator[x]) for x in database.translator}
    repeats = set()
    for key in range(0, len(list(database.translator.keys())) - 1):
        for key2 in range(key + 1, len(list(database.translator.keys()))):
            if (
                stringrep[list(database.translator.keys())[key]]
                == stringrep[list(database.translator.keys())[key2]]
            ):
                repeats.add(
                    (
                        list(database.translator.keys())[key],
                        list(database.translator.keys())[key2],
                    )
                )
    removed = []
    for repeat in repeats:
        temp = sorted(repeat)
        logMess(
            "ERROR:SCT241",
            "{0}:{1}:produce the same translation:{2}:{1}:was empied".format(
                temp[0], temp[1], database.prunnedDependencyGraph[temp[0]][0]
            ),
        )
        if temp[1] in list(database.translator.keys()) and repeat[1] not in removed:
            database.translator.pop(repeat[1])
            removed.append(repeat[1])


def transformMolecules(
    parser,
    database,
    configurationFile,
    namingConventions,
    speciesEquivalences=None,
    bioGridFlag=False,
    memoizedResolver=True,
):
    """
    main method. Receives a parser configuration, a configurationFile and a
    list of user defined species equivalences and returns a dictionary
    containing an atomized version of the model
    Args:
        parser: data structure containing the reactions and species we will use
        database: data structure containining the result of the outgoing translation
        configurationFile:
        speciesEquivalences: predefined species
    """
    """
    import cProfile, pstats, StringIO
    pr = cProfile.Profile()
    pr.enable()
    """
    database.parser = parser
    # ASS - Gotta pass in the option to memoize here
    sctsolver = resolveSCT.SCTSolver(database, memoizedResolver)
    database = sctsolver.createSpeciesCompositionGraph(
        parser,
        configurationFile,
        namingConventions,
        speciesEquivalences=speciesEquivalences,
        bioGridFlag=bioGridFlag,
    )

    for element in database.artificialEquivalenceTranslator:
        if element not in database.eequivalenceTranslator:
            database.eequivalenceTranslator[element] = []
        database.eequivalenceTranslator[element].extend(
            database.artificialEquivalenceTranslator[element]
        )

    # special handling for double modifications like double phosporylation
    # FIXME: this needs to be done in a cleaner way(e.g. getting them
    # from a file instead of being hardcoded)
    doubleModifications = {"Double-Phosporylation": "Phosporylation"}

    for element in doubleModifications:

        if doubleModifications[element] not in database.eequivalenceTranslator:
            continue
        if element not in database.eequivalenceTranslator:
            database.eequivalenceTranslator[element] = []

        baseElements = [
            x[0] for x in database.eequivalenceTranslator[doubleModifications[element]]
        ]
        modifiedElements = [
            x[1] for x in database.eequivalenceTranslator[doubleModifications[element]]
        ]
        # deleteEquivalences = [baseElements.index(x) for x in baseElements if x in modifiedElements]

        deleteEquivalences = [
            (x, modifiedElements[baseElements.index(x)])
            for x in baseElements
            if x in modifiedElements
        ]

        for eq in deleteEquivalences:
            if eq not in database.eequivalenceTranslator[element]:
                database.eequivalenceTranslator[element].append(eq)

        for eq in deleteEquivalences:

            if eq in database.eequivalenceTranslator[doubleModifications[element]]:
                database.eequivalenceTranslator[doubleModifications[element]].remove(eq)

    for modification in database.tmpEquivalence:
        for candidates in database.tmpEquivalence[modification]:
            for instance in candidates:
                atoAux.addToDependencyGraph(
                    database.eequivalenceTranslator, modification, instance
                )

    database.weights = sorted(
        database.weights, key=lambda rule: (rule[1], len(rule[0]))
    )
    atomize(
        database.prunnedDependencyGraph,
        database.weights,
        database.translator,
        database.reactionProperties,
        database.eequivalenceTranslator2,
        bioGridFlag,
        database.sbmlAnalyzer,
        database,
        parser,
    )
    onlySynDec = (
        len([x for x in database.classifications if x not in ["Generation", "Decay"]])
        == 0
    )
    propagateChanges(database.translator, database.prunnedDependencyGraph)

    # check for isomorphism
    sanityCheck(database)
    """
    pr.disable()
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(10)
    print s.getvalue()
    """
    # database.assumptions = deepcopy(assumptions)
    # assumptions.clear()
    # ASS: Adding atomized new molecules to the molecule list
    for molecule in database.translator.keys():
        if molecule not in database.parser.used_molecules:
            database.parser.used_molecules.append(molecule)

    return database.translator, onlySynDec
