# -*- coding: utf-8 -*-
"""
Created on Fri Mar  1 16:14:42 2013

@author: proto
"""

#!/usr/bin/env python
from collections import OrderedDict
import time
import libsbml
import bionetgen.atomizer.writer.bnglWriter as writer
from optparse import OptionParser
import bionetgen.atomizer.atomizer.moleculeCreation as mc
import sys
from os import listdir
import re
import pickle
import copy

log = {"species": [], "reactions": []}
from collections import Counter, namedtuple

import bionetgen.atomizer.utils.structures as structures
from bionetgen.atomizer.utils.util import (
    logMess,
    setupLog,
    setupStreamLog,
    finishStreamLog,
    TranslationException,
)
from bionetgen.atomizer.utils import consoleCommands
from bionetgen.atomizer.sbml2bngl import SBML2BNGL

# from biogrid import loadBioGridDict as loadBioGrid
import logging
from bionetgen.atomizer.rulifier import postAnalysis
import pprint
import fnmatch
from collections import defaultdict

import sympy
from sympy.printing.str import StrPrinter
from sympy.core.sympify import SympifyError

# returntype for the sbml analyzer translator and helper functions
AnalysisResults = namedtuple(
    "AnalysisResults",
    [
        "rlength",
        "slength",
        "reval",
        "reval2",
        "clength",
        "rdf",
        "finalString",
        "speciesDict",
        "database",
        "annotation",
    ],
)


def loadBioGrid():
    pass


def handler(signum, frame):
    print("Forever is over!")
    raise Exception("end of time")


def getFiles(directory, extension):
    """
    Gets a list of bngl files that could be correctly translated in a given 'directory'

    Keyword arguments:
    directory -- The directory we will recurseviley get files from
    extension -- A file extension filter
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, "*.{0}".format(extension)):
            filepath = os.path.abspath(os.path.join(root, filename))
            matches.append([filepath, os.path.getsize(os.path.join(root, filename))])

    # sort by size
    # matches.sort(key=lambda filename: filename[1], reverse=False)

    matches = [x[0] for x in matches]

    return matches


import os.path


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def evaluation(numMolecules, translator):
    originalElements = numMolecules
    nonStructuredElements = len([1 for x in translator if "()" in str(translator[x])])
    if originalElements > 0:
        ruleElements = (
            (len(translator) - nonStructuredElements) * 1.0 / originalElements
        )
        if ruleElements > 1:
            ruleElements = (
                (len(translator) - nonStructuredElements) * 1.0 / len(translator.keys())
            )

    else:
        ruleElements = 0
    return ruleElements


def selectReactionDefinitions(bioNumber):
    """
    This method rrough the stats-biomodels database looking for the
    best reactionDefinitions definition available
    """
    # with open('stats4.npy') as f:
    #    db = pickle.load(f)
    fileName = resource_path("config/reactionDefinitions.json")
    useID = True
    naming = resource_path("config/namingConventions.json")
    """
    for element in db:
        if element[0] == bioNumber and element[1] != '0':
            fileName = 'reactionDefinitions/reactionDefinition' + element[1] + '.json'
            useID = element[5]
        elif element[0] > bioNumber:
            break
    """
    return fileName, useID, naming


def resolveDependencies(dictionary, key, idx):
    counter = 0
    for element in dictionary[key]:
        if idx < 20:
            counter += resolveDependencies(dictionary, element, idx + 1)
        else:
            counter += 1
    return len(dictionary[key]) + counter


def validateReactionUsage(reactant, reactions):
    for element in reactions:
        if reactant in element:
            return element
    return None


def readFromString(
    inputString,
    reactionDefinitions,
    useID,
    speciesEquivalence=None,
    atomize=False,
    loggingStream=None,
    replaceLocParams=True,
):
    """
    one of the library's main entry methods. Process data from a string
    """

    console = None
    if loggingStream:
        console = logging.StreamHandler(loggingStream)
        console.setLevel(logging.DEBUG)

        setupStreamLog(console)

    reader = libsbml.SBMLReader()
    document = reader.readSBMLFromString(inputString)
    parser = SBML2BNGL(document.getModel(), useID, replaceLocParams=replaceLocParams)

    bioGrid = False
    pathwaycommons = True
    if bioGrid:
        loadBioGrid()

    database = structures.Databases()
    database.assumptions = defaultdict(set)
    database.document = document
    database.forceModificationFlag = True
    database.reactionDefinitions = reactionDefinitions
    database.useID = useID
    database.atomize = atomize
    database.speciesEquivalence = speciesEquivalence
    database.pathwaycommons = True
    database.isConversion = True
    # if pathwaycommons:
    #    database.pathwaycommons = True
    namingConventions = resource_path("config/namingConventions.json")

    if atomize:
        translator, onlySynDec = mc.transformMolecules(
            parser,
            database,
            reactionDefinitions,
            namingConventions,
            speciesEquivalence,
            bioGrid,
        )
        database.species = translator.keys()
    else:
        translator = {}
    # logging.getLogger().flush()
    if loggingStream:
        finishStreamLog(console)
    returnArray = analyzeHelper(
        document,
        reactionDefinitions,
        useID,
        "",
        speciesEquivalence,
        atomize,
        translator,
        database,
        replaceLocParams=replaceLocParams,
    )

    if atomize and onlySynDec:
        returnArray = list(returnArray)
    returnArray = AnalysisResults(
        *(list(returnArray[0:-2]) + [database] + [returnArray[-1]])
    )

    return returnArray


def processFunctions(functions, sbmlfunctions, artificialObservables, tfunc):
    """
    this method goes through the list of functions and removes all
    sbml elements that are extraneous to bngl
    """
    # reformat time function
    for idx in range(0, len(functions)):
        """
        remove calls to functions inside functions
        """
        modificationFlag = True
        recursionIndex = 0
        # remove calls to other sbml functions
        while modificationFlag and recursionIndex < 20:
            modificationFlag = False
            for sbml in sbmlfunctions:
                if sbml in functions[idx]:
                    temp = writer.extendFunction(
                        functions[idx], sbml, sbmlfunctions[sbml]
                    )
                    if temp != functions[idx]:
                        functions[idx] = temp
                        modificationFlag = True
                        recursionIndex += 1
                        break

        functions[idx] = re.sub(r"(\W|^)(time)(\W|$)", r"\1time()\3", functions[idx])
        functions[idx] = re.sub(r"(\W|^)(Time)(\W|$)", r"\1time()\3", functions[idx])
        functions[idx] = re.sub(r"(\W|^)(t)(\W|$)", r"\1time()\3", functions[idx])

        # remove true and false
        functions[idx] = re.sub(r"(\W|^)(true)(\W|$)", r"\1 1\3", functions[idx])
        functions[idx] = re.sub(r"(\W|^)(false)(\W|$)", r"\1 0\3", functions[idx])
    # functions.extend(sbmlfunctions)
    dependencies2 = {}
    for idx in range(0, len(functions)):
        dependencies2[functions[idx].split(" = ")[0].split("(")[0].strip()] = []
        for key in artificialObservables:
            oldfunc = functions[idx]
            functions[idx] = re.sub(
                r"(\W|^)({0})([^\w(]|$)".format(key), r"\1\2()\3", functions[idx]
            )
            if oldfunc != functions[idx]:
                dependencies2[functions[idx].split(" = ")[0].split("(")[0]].append(key)
        for element in sbmlfunctions:
            oldfunc = functions[idx]
            key = element.split(" = ")[0].split("(")[0]
            if (
                re.search("(\W|^){0}(\W|$)".format(key), functions[idx].split(" = ")[1])
                != None
            ):
                dependencies2[functions[idx].split(" = ")[0].split("(")[0]].append(key)
        for element in tfunc:
            key = element.split(" = ")[0].split("(")[0]
            if key in functions[idx].split(" = ")[1]:
                dependencies2[functions[idx].split(" = ")[0].split("(")[0]].append(key)
    """
    for counter in range(0, 3):
        for element in dependencies2:
            if len(dependencies2[element]) > counter:
                dependencies2[element].extend(dependencies2[dependencies2[element][counter]])
    """

    fd = []
    for function in functions:
        # print(function, '---', dependencies2[function.split(' = ' )[0].split('(')[0]], '---', function.split(' = ' )[0].split('(')[0], 0)
        fd.append(
            [
                function,
                resolveDependencies(
                    dependencies2, function.split(" = ")[0].split("(")[0], 0
                ),
            ]
        )
    fd = sorted(fd, key=lambda rule: rule[1])
    functions = [x[0] for x in fd]

    return functions


def extractAtoms(species):
    """
    given a list of structures, returns a list
    of individual molecules/compartment pairs
    appends a number for
    """
    listOfAtoms = set()
    for molecule in species.molecules:
        for component in molecule.components:
            listOfAtoms.add(tuple([molecule.name, component.name]))
    return listOfAtoms


def bondPartners(species, bondNumber):
    relevantComponents = []
    for molecule in species.molecules:
        for component in molecule.components:
            if bondNumber in component.bonds:
                relevantComponents.append(tuple([molecule.name, component.name]))
    return relevantComponents


def getMoleculeByName(species, atom):
    """
    returns the state of molecule-component contained in atom
    """

    stateVectorVector = []
    for molecule in species.molecules:
        if molecule.name == atom[0]:
            stateVector = []
            for component in molecule.components:
                if component.name == atom[1]:

                    # get whatever species this atom is bound to
                    if len(component.bonds) > 0:
                        comp = bondPartners(species, component.bonds[0])
                        comp.remove(atom)
                        if len(comp) > 0:
                            stateVector.append(comp[0])
                        else:
                            stateVector.append("")
                    else:
                        stateVector.append("")
                    if len(component.states) > 0:
                        stateVector.append(component.activeState)
                    else:
                        stateVector.append("")
            stateVectorVector.append(stateVector)
    return tuple(stateVectorVector[0])


def extractCompartmentCoIncidence(species):
    atomPairDictionary = {}
    if [x.name for x in species.molecules] == ["EGF", "EGF", "EGFR", "EGFR"]:
        pass
    for molecule in species.molecules:
        for component in molecule.components:
            for component2 in molecule.components:
                if component == component2:
                    continue
                atom = tuple([molecule.name, component.name])
                atom2 = tuple([molecule.name, component2.name])
                molId1 = getMoleculeByName(species, atom)
                molId2 = getMoleculeByName(species, atom2)
                key = tuple([atom, atom2])
                # print(key, (molId1, molId2))
                if key not in atomPairDictionary:
                    atomPairDictionary[key] = Counter()
                atomPairDictionary[key].update([tuple([molId1, molId2])])

    return atomPairDictionary


def extractCompartmentStatistics(
    bioNumber, useID, reactionDefinitions, speciesEquivalence
):
    """
    Iterate over the translated species and check which compartments
    are used together, and how.
    """
    reader = libsbml.SBMLReader()
    document = reader.readSBMLFromFile(bioNumber)

    parser = SBML2BNGL(document.getModel(), useID)
    database = structures.Databases()
    database.pathwaycommons = False
    # call the atomizer (or not)
    # if atomize:
    translator, onlySynDec = mc.transformMolecules(
        parser, database, reactionDefinitions, speciesEquivalence
    )
    # else:
    #    translator={}

    compartmentPairs = {}
    for element in translator:
        temp = extractCompartmentCoIncidence(translator[element])
        for element in temp:
            if element not in compartmentPairs:
                compartmentPairs[element] = temp[element]
            else:
                compartmentPairs[element].update(temp[element])
    finalCompartmentPairs = {}
    print("-----")
    for element in compartmentPairs:
        if element[0][0] not in finalCompartmentPairs:
            finalCompartmentPairs[element[0][0]] = {}
        finalCompartmentPairs[element[0][0]][
            tuple([element[0][1], element[1][1]])
        ] = compartmentPairs[element]
    return finalCompartmentPairs


def recursiveSearch(dictionary, element, visitedFunctions=[]):
    tmp = 0
    for item in dictionary[element]:
        if dictionary[item] == []:
            tmp += 1
        else:
            if item in visitedFunctions:
                raise Exception(
                    "Recursive function search landed twice in the same function"
                )
            tmp += 1
            tmp += recursiveSearch(dictionary, item, [item] + visitedFunctions)
    return tmp


def reorder_and_replace_arules(functions, parser):
    # TODO: Check if we need full_prec, make it optional
    prnter = StrPrinter({"full_prec": False})
    func_names = []
    # get full func names and initialize dependency graph
    dep_dict = {}
    for func in functions:
        splt = func.split("=")
        n = splt[0]
        f = "=".join(splt[1:])
        name = n.rstrip().replace("()", "")
        func_names.append(name)
        if "fRate" not in name:
            dep_dict[name] = []
    # make dependency graph between funcs only
    func_dict = {}
    new_funcs = []
    # Let's replace and build dependency map
    frates = []
    for func in functions:
        splt = func.split("=")
        # TODO: turn this into warning
        n = splt[0]
        f = "=".join(splt[1:])
        fname = n.rstrip().replace("()", "")
        try:
            fs = sympy.sympify(f, locals=parser.all_syms)
        except:
            # Can't parse this func
            if fname.startswith("fRate"):
                frates.append((fname.strip(), f))
            else:
                func_dict[fname] = f
            continue
        # replace here since it affects dependency
        for item in parser.only_assignment_dict.items():
            oname, nname = item
            osym, ns = sympy.symbols(oname + "," + nname)
            fs = fs.subs(osym, ns)
        func_dict[fname] = fs
        # need to build a dependency graph to figure out what to
        # write first
        # We can skip this if it's a functionRate
        if "fRate" not in n:
            list_of_deps = list(map(str, fs.atoms(sympy.Symbol)))
            for dep in list_of_deps:
                if dep in func_names:
                    dep_dict[fname].append(dep)
        else:
            frates.append((n.strip(), fs))
    # Now reorder accordingly
    ordered_funcs = []
    # this ensures we write the independendent functions first
    stck = sorted(dep_dict.keys(), key=lambda x: len(dep_dict[x]))
    # FIXME: This algorithm works but likely inefficient
    while len(stck) > 0:
        k = stck.pop()
        deps = dep_dict[k]
        if len(deps) == 0:
            if k not in ordered_funcs:
                ordered_funcs.append(k)
        else:
            stck.append(k)
            for dep in deps:
                if dep not in ordered_funcs:
                    stck.append(dep)
                dep_dict[k].remove(dep)
    # print ordered functions and return
    for fname in ordered_funcs:
        fs = func_dict[fname]
        # clean up some whitespace here
        try:
            func_str = prnter.doprint(fs)
            func_str = func_str.replace("**", "^")
            new_funcs.append(fname + "() = " + func_str)
        except:
            new_funcs.append(fname + "() = " + fs)
    # now write the functionRates
    for fitem in frates:
        n, fs = fitem
        func_str = prnter.doprint(fs)
        func_str = func_str.replace("**", "^")
        new_funcs.append(n + " = " + func_str)
    return new_funcs


def reorderFunctions(functions):
    """
    Analyze a list of sbml functions and make sure there are no forward dependencies.
    Reorder if necessary
    """
    functionNames = []
    tmp = []
    for function in functions:

        m = re.split("(?<=\()[\w)]", function)
        functionName = m[0]
        if "=" in functionName:
            functionName = functionName.split("=")[0].strip() + "("
        functionNames.append(functionName)
    functionNamesDict = {x: [] for x in functionNames}
    for idx, function in enumerate(functions):
        tmp = [
            x
            for x in functionNames
            if x in function.split("=")[1] and x != functionNames[idx]
        ]
        functionNamesDict[functionNames[idx]].extend(tmp)
    newFunctionNamesDict = {}
    for name in functionNamesDict:
        try:
            newFunctionNamesDict[name] = recursiveSearch(functionNamesDict, name, [])
        # there is a circular dependency
        except:
            newFunctionNamesDict[name] = 99999
    functionWeightsDict = {x: newFunctionNamesDict[x] for x in newFunctionNamesDict}
    functionWeights = []
    for name in functionNames:
        functionWeights.append(functionWeightsDict[name])
    tmp = zip(functions, functionWeights)
    idx = sorted(tmp, key=lambda x: x[1])
    return [x[0] for x in idx]


def postAnalysisHelper(outputFile, bngLocation, database):
    consoleCommands.setBngExecutable(bngLocation)
    outputDir = os.sep.join(outputFile.split(os.sep)[:-1])
    if outputDir != "":
        retval = os.getcwd()
        os.chdir(outputDir)
    consoleCommands.bngl2xml(outputFile.split(os.sep)[-1])
    if outputDir != "":
        os.chdir(retval)
    bngxmlFile = ".".join(outputFile.split(".")[:-1]) + ".xml"
    # print('Sending BNG-XML file to context analysis engine')
    contextAnalysis = postAnalysis.ModelLearning(bngxmlFile)
    # analysis of redundant bonds
    deleteBonds = contextAnalysis.analyzeRedundantBonds(
        database.assumptions["redundantBonds"]
    )
    for molecule in database.assumptions["redundantBondsMolecules"]:
        if molecule[0] in deleteBonds:
            for bond in deleteBonds[molecule[0]]:
                database.translator[molecule[1]].deleteBond(bond)
                logMess(
                    "INFO:CTX002",
                    "Used context information to determine that the bond {0} in species {1} is not likely".format(
                        bond, molecule[1]
                    ),
                )


def postAnalyzeFile(outputFile, bngLocation, database, replaceLocParams=True):
    """
    Performs a postcreation file analysis based on context information
    """
    # print('Transforming generated BNG file to BNG-XML representation for analysis')

    postAnalysisHelper(outputFile, bngLocation, database)

    # recreate file using information from the post analysis
    returnArray = analyzeHelper(
        database.document,
        database.reactionDefinitions,
        database.useID,
        outputFile,
        database.speciesEquivalence,
        database.atomize,
        database.translator,
        database,
        replaceLocParams=replaceLocParams,
    )
    with open(outputFile, "w") as f:
        f.write(returnArray.finalString)
    # recompute bng-xml file
    consoleCommands.bngl2xml(outputFile)
    bngxmlFile = ".".join(outputFile.split(".")[:-1]) + ".xml"
    # recompute context information
    contextAnalysis = postAnalysis.ModelLearning(bngxmlFile)

    # get those species patterns that follow uncommon motifs
    motifSpecies, motifDefinitions = contextAnalysis.processContextMotifInformation(
        database.assumptions["lexicalVsstoch"], database
    )
    # motifSpecies, motifDefinitions = contextAnalysis.processAllContextInformation()
    if len(motifDefinitions) > 0:
        logMess(
            "INFO:CTX003",
            "Species with suspect context information were found. Information is being dumped to {0}_context.log".format(
                outputFile
            ),
        )
        with open("{0}_context.log".format(outputFile), "w") as f:
            pprint.pprint(dict(motifSpecies), stream=f)
            pprint.pprint(motifDefinitions, stream=f)

    # score hypothetical bonds
    # contextAnalysis.scoreHypotheticalBonds(assumptions['unknownBond'])


def postAnalyzeString(outputFile, bngLocation, database):
    postAnalysisHelper(outputFile, bngLocation, database)

    # recreate file using information from the post analysis
    returnArray = analyzeHelper(
        database.document,
        database.reactionDefinitions,
        database.useID,
        outputFile,
        database.speciesEquivalence,
        database.atomize,
        database.translator,
        database,
    ).finalString
    return returnArray


def analyzeFile(
    bioNumber,
    reactionDefinitions,
    useID,
    namingConventions,
    outputFile,
    speciesEquivalence=None,
    atomize=False,
    bioGrid=False,
    pathwaycommons=False,
    ignore=False,
    noConversion=False,
    memoizedResolver=True,
    replaceLocParams=True,
    quietMode=False,
    logLevel="WARNING",
):
    """
    one of the library's main entry methods. Process data from a file
    """
    """
    import cProfile, pstats, StringIO
    pr = cProfile.Profile()
    pr.enable()
    """
    setupLog(
        outputFile + ".log", getattr(logging, logLevel.upper()), quietMode=quietMode
    )

    logMess.log = []
    logMess.counter = -1
    reader = libsbml.SBMLReader()
    document = reader.readSBMLFromFile(bioNumber)

    if document.getModel() == None:
        print("File {0} could not be recognized as a valid SBML file".format(bioNumber))
        return
    parser = SBML2BNGL(document.getModel(), useID, replaceLocParams=replaceLocParams)
    parser.setConversion(not noConversion)
    database = structures.Databases()
    database.assumptions = defaultdict(set)
    database.forceModificationFlag = True
    database.pathwaycommons = pathwaycommons
    database.ignore = ignore
    database.assumptions = defaultdict(set)

    bioGridDict = {}
    if bioGrid:
        bioGridDict = loadBioGrid()

    # call the atomizer (or not). structured molecules are contained in translator
    # onlysyndec is a boolean saying if a model is just synthesis of decay reactions
    # ASS2019 - With this try/except the translator was not being initialized and led to an undefined error in certain models

    translator = {}
    try:
        if atomize:
            translator, onlySynDec = mc.transformMolecules(
                parser,
                database,
                reactionDefinitions,
                namingConventions,
                speciesEquivalence,
                bioGrid,
                memoizedResolver,
            )
    except TranslationException as e:
        print(
            "Found an error in {0}. Check log for more details. Use -I to ignore translation errors".format(
                e.value
            )
        )
        if len(logMess.log) > 0:
            with open(outputFile + ".log", "w") as f:
                for element in logMess.log:
                    f.write(element + "\n")
        return

    # process other sections of the sbml file (functions reactions etc.)
    """
    pr.disable()
    s = StringIO.StringIO()
    sortby = 'cumulative'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats(10)
    print(s.getvalue())
    """
    database.document = document
    database.reactionDefinitions = reactionDefinitions
    database.useID = useID
    database.speciesEquivalence = speciesEquivalence
    database.atomize = atomize
    database.isConversion = not noConversion

    returnArray = analyzeHelper(
        document,
        reactionDefinitions,
        useID,
        outputFile,
        speciesEquivalence,
        atomize,
        translator,
        database,
        replaceLocParams=replaceLocParams,
    )

    with open(outputFile, "w") as f:
        f.write(returnArray.finalString)
    # with open('{0}.dict'.format(outputFile), 'wb') as f:
    #    pickle.dump(returnArray[-1], f)
    if atomize and onlySynDec:
        returnArray = list(returnArray)
        # returnArray.translator = -1
    returnArray = AnalysisResults(
        *(list(returnArray[0:-2]) + [database] + [returnArray[-1]])
    )
    return returnArray


def correctRulesWithParenthesis(rules, parameters):
    """
    helper function. Goes through a list of rules and adds a parenthesis
    to the reaction rates of those functions whose rate is in list
    'parameters'.
    """
    for idx in range(len(rules)):
        tmp = [x for x in parameters if x + " " in rules[idx]]
        # for tmpparameter in tmp:
        #    re.sub(r'(\W|^){0}(\W|$)'.format(tmpparameter), r'\1{0}\2'.format(dictionary[key]), tmp[1])
        if len(tmp) > 0:
            rules[idx].strip()
            rules[idx] += "()"


def changeNames(functions, dictionary):
    """
    changes instances of keys in dictionary appeareing in functions to their corresponding
    alternatives
    """
    tmpArray = []
    for function in functions:
        tmp = function.split(" = ")
        # hack to avoid problems with less than equal or more than equal
        # in equations

        # ASS2019 - There are cases where we have more than one equal sign e.g. "= = 0&&"
        # in an if statement, I _think_ we need to re-add the '=' we removed by doing
        # split
        tmp = [tmp[0], "=".join(tmp[1:])]
        for key in [x for x in dictionary if x in tmp[1]]:
            # ASS - if the key is equal to the value, this goes for an infinite loop
            if key == dictionary[key]:
                continue
            while re.search(r"([\W, ]|^){0}([\W, ]|$)".format(key), tmp[1]):
                tmp[1] = re.sub(
                    r"([\W, ]|^){0}([\W, ]|$)".format(key),
                    r"\1{0}\2".format(dictionary[key]),
                    tmp[1],
                )
        tmpArray.append("{0} = {1}".format(tmp[0], tmp[1]))
    return tmpArray


# ASS - We need to rename the functions if they are the same as obs
def changeDefs(functions, dictionary):
    """
    changes the names of the functions (RHS) instead of the LHS
    """
    tmpArray = []
    for function in functions:
        tmp = function.split(" = ")
        # hack to avoid problems with less than equal or more than equal
        # in equations
        tmp = [tmp[0], "".join(tmp[1:])]
        for key in [x for x in dictionary if x in tmp[0]]:
            # ASS - if the key is equal to the value, this goes for an infinite loop
            if key == dictionary[key]:
                continue
            while re.search(r"([\W, ]|^){0}([\W, ]|$)".format(key), tmp[0]):
                tmp[0] = re.sub(
                    r"([\W, ]|^){0}([\W, ]|$)".format(key),
                    r"\1{0}\2".format(dictionary[key]),
                    tmp[0],
                )
        tmpArray.append("{0} = {1}".format(tmp[0], tmp[1]))
    return tmpArray


def changeRates(reactions, dictionary):
    """
    changes instances of keys in dictionary appeareing in reaction rules to their corresponding
    alternatives
    """
    tmpArray = []
    tmp = None
    for reaction in reactions:
        cmt = None
        tmp = reaction.strip().split(" ")
        for ielem, elem in enumerate(tmp):
            if elem.startswith("#"):
                cmt = tmp[ielem:]
                tmp = tmp[:ielem]
                break
        for key in [x for x in dictionary if x in tmp[-1]]:
            tmp[-1] = re.sub(
                r"(\W|^){0}(\W|$)".format(key),
                r"\1{0}\2".format(dictionary[key]),
                tmp[-1],
            )
        if cmt is not None:
            tmp += cmt
        tmpArray.append(" ".join(tmp))
    # if tmp:
    #     if cmt is not None:
    #         tmp += cmt
    #     tmpArray.append(' '.join(tmp))
    return tmpArray


def unrollFunctions(functions):
    flag = True
    # bngl doesnt accept nested function calling
    while flag:
        dictionary = OrderedDict()
        flag = False
        for function in functions:
            tmp = function.split(" = ")
            for key in dictionary:
                if key in tmp[1]:
                    tmp[1] = re.sub(
                        r"(\W|^){0}\(\)(\W|$)".format(key),
                        r"\1({0})\2".format(dictionary[key]),
                        tmp[1],
                    )
                    flag = False
            dictionary[tmp[0].split("()")[0]] = tmp[1]
        tmp = []
        for key in dictionary:
            tmp.append("{0}() = {1}".format(key, dictionary[key]))
        functions = tmp
    return functions


def analyzeHelper(
    document,
    reactionDefinitions,
    useID,
    outputFile,
    speciesEquivalence,
    atomize,
    translator,
    database,
    bioGrid=False,
    replaceLocParams=True,
):
    """
    taking the atomized dictionary and a series of data structure, this method
    does the actual string output.
    """
    useArtificialRules = False
    parser = SBML2BNGL(document.getModel(), useID, replaceLocParams=replaceLocParams)
    # ASS: Port over other parsers? used_molecules list
    if hasattr(database, "parser"):
        parser.used_molecules.extend(database.parser.used_molecules)
    parser.setConversion(database.isConversion)
    #
    param, zparam = parser.getParameters()
    rawSpecies = {}
    for species in parser.model.getListOfSpecies():
        rawtemp = parser.getRawSpecies(species, [x.split(" ")[0] for x in param])
        rawSpecies[rawtemp["identifier"]] = rawtemp
    parser.reset()

    # parser.bngModel.translator = copy.deepcopy(translator)
    parser.bngModel.translator = translator
    (
        molecules,
        initialConditions,
        observables,
        speciesDict,
        observablesDict,
        annotationInfo,
    ) = parser.getSpecies(translator, [x.split(" ")[0] for x in param])

    # finally, adjust parameters and initial concentrations according to whatever  initialassignments say
    param, zparam, initialConditions = parser.getInitialAssignments(
        translator, param, zparam, molecules, initialConditions
    )

    # FIXME: this method is a mess, improve handling of assignmentrules since we can actually handle those
    (
        aParameters,
        aRules,
        nonzparam,
        artificialRules,
        removeParams,
        artificialObservables,
    ) = parser.getAssignmentRules(
        zparam, param, rawSpecies, observablesDict, translator
    )

    compartments = parser.getCompartments()
    functions = []
    assigmentRuleDefinedParameters = []

    # FIXME: We should determine if an assignment rule
    # if being used along with a reaction and ignore the
    # reaction if it is being modified by both. This will
    # likely require us to feed something from the assingment
    # rule result into the following function
    reactionParameters, rules, rateFunctions = parser.getReactions(
        translator,
        len(compartments) > 1,
        atomize=atomize,
        parameterFunctions=artificialObservables,
        database=database,
    )

    functions.extend(rateFunctions)

    for element in nonzparam:
        param.append("{0} 0".format(element))
    param = [x for x in param if x not in removeParams]

    # tags = '@{0}'.format(compartments[0].split(' ')[0]) if len(compartments) == 1 else '@cell'
    # ASS - trying to remove @cell as a default compartment. Also, 0th compartment
    # is generally a comment. Here we are taking the first non-comment compartment as
    # the default compartment if we are missing the compartment, generally for
    # SBML non-constant parameter starting values.
    if len(compartments) == 0:
        def_compartment = ""
    elif len(compartments) == 1:
        def_compartment = compartments[0].split(" ")[0]
    else:
        for compartment in compartments:
            if not compartment.startswith("#"):
                def_compartment = compartment.split(" ")[0]
                break
    if def_compartment != "":
        tags = "@{0}".format(def_compartment)
    else:
        tags = ""

    # We need to replace stuff that we have a definition for
    # if they are used in assignment rules
    art_names = dict([(key[:-3], key) for key in artificialObservables])
    for key in artificialObservables:
        changed = False
        f = artificialObservables[key]

        fsplt = f.split("=")
        fn = fsplt[0]
        fd = "=".join(fsplt[1:])
        for an in art_names:
            # We need an exact match
            if re.search("\b{}\b".format(an), fd) is not None:
                fd = re.sub("\b{}\b".format(an), art_names[an], fd)
                changed = True
        if changed:
            artificialObservables[key] = fn.split()[0] + " = " + fd
    # Here we are adding removed parameters back as
    # molecules, species and observables? How do we know
    # we need these?
    for remPar in removeParams:
        par_nam = remPar.split()[0]
        write = True
        # Check assignment rules first
        for key in artificialObservables:
            if (par_nam == key) or (par_nam + "_ar" == key):
                # We have an assignment rule for this parameter
                # and we don't want to have molecules and stuff
                write = False
                break
        if write:
            if par_nam not in molecules:
                molecules.append(par_nam)
            obs_str = "Species {0} {0}".format(par_nam)
            if obs_str not in molecules:
                observables.append(obs_str)
            init_cond = par_nam + tags + " " + " ".join(remPar.split()[1:])
            if init_cond not in initialConditions:
                initialConditions.append(init_cond)
    ## Comment out those parameters that are defined with assignment rules
    ## TODO: I think this is correct, but it may need to be checked
    tmpParams = []
    for idx, parameter in enumerate(param):
        for key in artificialObservables:
            if re.search("^{0}\s".format(key), parameter) != None:
                assigmentRuleDefinedParameters.append(idx)
    tmpParams.extend(artificialObservables)
    tmpParams.extend(removeParams)
    tmpParams = set(tmpParams)
    correctRulesWithParenthesis(rules, tmpParams)

    for element in assigmentRuleDefinedParameters:
        param[element] = "#" + param[element]

    deleteMolecules = []
    deleteMoleculesFlag = True

    for key in artificialObservables:
        flag = -1
        for idx, observable in enumerate(observables):
            if "Species {0} {0}()".format(key) in observable:
                flag = idx
        if flag != -1:
            observables.pop(flag)
        functions.append(artificialObservables[key])
        flag = -1

        if "{0}()".format(key) in molecules:
            flag = molecules.index("{0}()".format(key))

        if flag != -1:
            if deleteMoleculesFlag:
                deleteMolecules.append(flag)
            else:
                deleteMolecules.append(key)
            # result =validateReactionUsage(molecules[flag], rules)
            # if result != None:
            #    logMess('ERROR', 'Pseudo observable {0} in reaction {1}'.format(molecules[flag], result))
            # molecules.pop(flag)

        flag = -1
        for idx, specie in enumerate(initialConditions):
            if ":{0}(".format(key) in specie:
                flag = idx
        if flag != -1:
            initialConditions[flag] = "#" + initialConditions[flag]

    for flag in sorted(deleteMolecules, reverse=True):

        if deleteMoleculesFlag:
            logMess(
                "WARNING:SIM101",
                "{0} reported as function, but usage is ambiguous".format(
                    molecules[flag]
                ),
            )
            result = validateReactionUsage(molecules[flag], rules)
            if result is not None:
                logMess(
                    "ERROR:Simulation",
                    "Pseudo observable {0} in reaction {1}".format(
                        molecules[flag], result
                    ),
                )

            # since we are considering it an observable delete it from the molecule and
            # initial conditions list
            # s = molecules.pop(flag)
            # initialConditions = [x for x in initialConditions if '$' + s not in x]
        else:
            logMess(
                "WARNING:SIM101",
                "{0} reported as species, but usage is ambiguous.".format(flag),
            )
            artificialObservables.pop(flag)

    sbmlfunctions = parser.getSBMLFunctions()
    functions.extend(aRules)

    parser.bngModel.sbmlFunctions = sbmlfunctions
    processFunctions(functions, sbmlfunctions, artificialObservables, rateFunctions)

    for interation in range(0, 3):
        for sbml2 in sbmlfunctions:
            for sbml in sbmlfunctions:
                if sbml == sbml2:
                    continue
                if sbml in sbmlfunctions[sbml2]:
                    sbmlfunctions[sbml2] = writer.extendFunction(
                        sbmlfunctions[sbml2], sbml, sbmlfunctions[sbml]
                    )

    # import IPython;IPython.embed()

    # TODO: if an observable is defined via artificial obs
    # we should overwrite it in obs dict
    for key in observablesDict:
        if key + "_ar" in artificialObservables:
            observablesDict[key] = key + "_ar"
    #
    functions = reorderFunctions(functions)
    #
    functions = changeNames(functions, aParameters)
    # change reference for observables with compartment name
    functions = changeNames(functions, observablesDict)
    #
    functions = unrollFunctions(functions)
    rules = changeRates(rules, aParameters)

    ar_names = {}
    # Some observables are encoded as functions
    for func in functions:
        fname = func.split("=")[0].split("(")[0]
        if fname.endswith("_ar"):
            potential_obs = fname.replace("_ar", "")
            if potential_obs in observablesDict:
                ar_names[potential_obs] = fname
    # Switch up AR stuff that's used as rate constants
    for item in observablesDict.items():
        k, t = item
        if t.endswith("_ar"):
            ar_names[k] = t
    rules = changeRates(rules, ar_names)

    # Parameter replacement leaves a lot of unevaluated
    # math behing and it looks really ugly. I'm going
    # to parse this and try to evaluate it all

    # TODO: This needs more love, I'm definitely not
    # handling certain things I normally handle in sbml2bnl
    # using sympy, port those in or turn them into importable
    # stuff
    # TODO: Check if full_prec is bad, make it optional
    prnter = StrPrinter({"full_prec": False})
    try:
        new_funcs = []
        obs_syms = list(map(sympy.Symbol, parser.obs_names))
        for func in functions:
            splt = func.split("=")
            n = splt[0]
            f = "=".join(splt[1:])
            n, f = splt
            try:
                fs = sympy.sympify(f, locals=parser.all_syms)
            except SympifyError:
                logMess(
                    "ERROR:SYMP002",
                    "Sympy can't parse a function during post-processing",
                )
                raise TranslationException(f)
            # Test if we get a complex i from simplification
            smpl = fs.nsimplify().evalf().simplify()
            # Epsilon checking
            n, d = smpl.as_numer_denom()
            # I don't want to touch the current rate parsing so
            # I'll remove it and then add it back if needed
            # TODO: mentioned above is a temporary solution
            had_epsilon = False
            if parser.all_syms["__epsilon__"] in d.atoms():
                d = d - parser.all_syms["__epsilon__"]
                had_epsilon = True
            # for item in parser.all_syms.items():
            for s in obs_syms:
                # k, s = item
                if s in d.atoms():
                    d = d.subs(s, 0)
            if d == 0:
                if had_epsilon:
                    new_f = prnter.doprint(smpl)
                else:
                    n, d = smpl.as_numer_denom()
                    logMess(
                        "WARNING:RATE001",
                        "Post-parameter replacement, the denominator can be 0, adding an epsilon to avoid discontinuities",
                    )
                    new_f = (
                        "("
                        + prnter.doprint(n)
                        + ")/("
                        + prnter.doprint(d)
                        + "+ __epsilon__)"
                    )
                    parser.write_epsilon = True
            else:
                new_f = prnter.doprint(smpl)
            new_f = new_f.replace("**", "^")
            # We want to do this if it makes the rate constant
            # more readable
            # FIXME: This doesn't mesh well with AR replacement
            # if len(new_f) < len(func):
            #    new_funcs.append(splt[0] + " = " + new_f)
            # else:
            #    new_funcs.append(func)
            new_funcs.append(splt[0] + " = " + new_f)
        functions = new_funcs
    except:
        # raise
        # This is not essential, let's just move on if
        # sympify fails. This catch-all is here because
        # I know there will be random small things and that
        # this bit is entirely optional
        pass

    functions = reorder_and_replace_arules(functions, parser)
    # ASS2019 - we need to adjust initial conditions of assignment rules
    # so that they start with the correct values. While this doesn't
    # impact model translation quality, it does make it difficult to
    # do automated testing
    initialConditions = parser.adjustInitialConditions(
        param, initialConditions, artificialObservables, observables, functions
    )

    # ASS - We need to check for identical observables and functions. If
    # they are the same, re-number them so avoid having identical names
    # this comes up when we do non-compartmental models only really
    # due to the naming scheme of STUFF_COMPNAME but still should be
    # handled somehow
    idenObsFuncDict = {}
    for obs in observables:
        obsKey = obs.split(" ")[1]
        for aObsKey in artificialObservables.keys():
            if obsKey == aObsKey:
                idenObsFuncDict[obsKey] = obsKey + "_func"

    functions = changeDefs(functions, idenObsFuncDict)

    if len(artificialRules) + len(rules) == 0:
        logMess("ERROR:SIM203", "The file contains no reactions")
    # ASS: This "useArtificialRules" flag can never be true
    # but artificial rules are being made and left unused
    # which is incorrect, at least in some cases e.g. BioMod 207
    if useArtificialRules or len(rules) == 0:
        rules = ["#{0}".format(x) for x in rules]
        artificialRules.extend(rules)
        rules = artificialRules
    if len(artificialRules) > 0:
        logMess(
            "WARNING:ARTR001",
            "The model contains rate rules which are modeled as rules in the BNGL translation.",
        )
        rules.extend(artificialRules)
    evaluate = evaluation(len(observables), translator)
    # else:
    #    artificialRules =['#{0}'.format(x) for x in artificialRules]
    #    evaluate =  evaluation(len(observables), translator)
    #    rules.extend(artificialRules)
    commentDictionary = {}

    # ASS: removing species that are not used
    # in BNGL species do not get adjusted by functions
    # therefore we can check the rules, if a species do not
    # appear anywhere in a rule, we can remove it
    # this will clean up a lot of translations
    # TODO: My approach to observables is too simplistic
    # obs can be a whole lot more complicated, ensure what
    # I'm doing actually works
    # TODO: Some species are not used in rules and are not fixed
    # BUT are then used in some functions. The original modeller
    # should have turned these into parameters but didn't. Let's
    # turn them into parameters? or leave them be?
    # also remove from seed species
    init_to_rem = []
    turn_to_param = []
    for iss, sspec in enumerate(initialConditions):
        comp = None
        splt = sspec.split()
        sname = splt[0]
        if splt[-1].startswith("#"):
            val = " ".join(splt[1:-2])
        else:
            val = " ".join(splt[1:])
        # let's see if we have a compartment
        if "@" in sname:
            plt = sname.split(":")
            if len(plt) > 1:
                # using @comp:spec notation
                sname = plt[1]
                comp = plt[0][1:]
            else:
                # using spec@comp notation
                sname, comp = sname.split("@")
        # remove $ if it's a fixed species
        if sname.startswith("$"):
            sname = sname[1:]
        # We want only the name
        if "(" in sname:
            sname = sname[: sname.find("(")]
        # let's see if it's actually used in rules
        if sname not in parser.used_molecules:
            # this is a "fixed molecule" that doesn't get used
            # in reactions. Let's check compartment and turn
            # into parameter instead
            # TODO: Sometimes the _comp version is used, sometimes
            # not, make it consistent
            if comp is not None:
                # we have a compartment
                turn_to_param.append(sname + "_{} ".format(comp) + val)
            turn_to_param.append(sname + " " + val)
        if sname not in parser.used_molecules:
            init_to_rem.append(sspec)
    for i in init_to_rem:
        initialConditions.remove(i)
    # Turn any "fixed molecules" that are not used in rules
    # into parameters
    param.extend(turn_to_param)
    # remove from molecules
    molec_to_rem = []
    for molec in molecules:
        # name
        if "(" in molec:
            mname = molec[: molec.find("(")]
        else:
            mname = molec
        # used or not?
        if mname not in parser.used_molecules:
            molec_to_rem.append(molec)
    for i in molec_to_rem:
        molecules.remove(i)
    # and observables
    obs_to_rem = []
    for iobs, obs_str in enumerate(observables):
        oname = obs_str.split()[2]
        comp = None
        if "@" in oname:
            if len(oname.split(":")) > 1:
                # using @comp:spec
                oname = oname.split(":")[1]
            else:
                # using spec@comp
                oname, comp = oname.split("@")
        if "(" in oname:
            oname = oname[: oname.find("(")]
        if oname not in parser.used_molecules:
            obs_to_rem.append(obs_str)
    for i in obs_to_rem:
        observables.remove(i)
    # done removing useless species/seed species/obs

    # TODO: temporary: check structured molecule ratio
    struc_count = 0
    for molec_str in molecules:
        srch = re.search(r"(\W|^)(.+)\((.*)\)", molec_str)
        if srch is not None:
            if len(srch.group(3)) > 0:
                struc_count += 1
    struc_ratio = float(struc_count) / len(molecules) if len(molecules) > 0 else 0
    # if struc_ratio == 0.5:
    # import IPython;IPython.embed()
    print("Structured molecule type ratio: {}".format(struc_ratio))

    # If we must, add __epsilon__ to parameter list
    if parser.write_epsilon:
        param = ["__epsilon__ 1e-100"] + param

    if atomize:
        commentDictionary[
            "notes"
        ] = "'This is an atomized translation of an SBML model created on {0}.".format(
            time.strftime("%d/%m/%Y")
        )
    else:
        commentDictionary[
            "notes"
        ] = "'This is a plain translation of an SBML model created on {0}.".format(
            time.strftime("%d/%m/%Y")
        )
    commentDictionary[
        "notes"
    ] += " The original model has {0} molecules and {1} reactions. The translated model has {2} molecules and {3} rules'".format(
        parser.model.getNumSpecies(),
        parser.model.getNumReactions(),
        len(molecules),
        len(set(rules)),
    )
    meta = parser.getMetaInformation(commentDictionary)
    finalString = writer.finalText(
        meta,
        param + reactionParameters,
        molecules,
        initialConditions,
        list(OrderedDict.fromkeys(observables)),
        list(OrderedDict.fromkeys(rules)),
        functions,
        compartments,
        annotationInfo,
        outputFile,
    )

    logMess(
        "INFO:SUM001",
        "File contains {0} molecules out of {1} original SBML species".format(
            len(molecules), len(observables)
        ),
    )

    # rate of each classified rule
    evaluate2 = 0 if len(observables) == 0 else len(molecules) * 1.0 / len(observables)

    # add unit information to annotations

    # print("in libsbml, done completely")
    # with open(outputFile, "w") as f:
    #     f.write(str(parser.bngModel))
    # import IPython;IPython.embed()
    parser.bngModel.all_syms = parser.all_syms
    parser.bngModel.consolidate()
    finalString = str(parser.bngModel)

    annotationInfo["units"] = parser.getUnitDefinitions()
    return AnalysisResults(
        len(rules),
        len(observables),
        evaluate,
        evaluate2,
        len(compartments),
        parser.getSpeciesAnnotation(),
        finalString,
        speciesDict,
        None,
        annotationInfo,
    )

    """
    if translator != {}:
        for element in database.classifications:
            if element not in classificationDict:
                classificationDict[element] = 0.0
            classificationDict[element] += 1.0/len(database.classifications)
        return len(rules), evaluate, parser.getModelAnnotation(), classificationDict
    """
    # return None, None, None, None


def processFile(translator, parser, outputFile):
    param2 = parser.getParameters()
    molecules, species, observables, observablesDict = parser.getSpecies(translator)
    compartments = parser.getCompartments()
    param, rules, functions = parser.getReactions(translator, True)
    param += param2
    writer.finalText(
        param,
        molecules,
        species,
        observables,
        rules,
        functions,
        compartments,
        {},
        outputFile,
    )


def BNGL2XML():
    pass


def getAnnotations(annotation):
    annotationDictionary = []
    if annotation == [] or annotation is None:
        return []
    for indivAnnotation in annotation:
        for index in range(0, indivAnnotation.getNumAttributes()):
            annotationDictionary.append(indivAnnotation.getValue(index))
    return annotationDictionary


def getAnnotationsDict(annotation):
    annotationDict = {}
    for element in annotation:
        annotationDict[element] = getAnnotations(annotation[element])
    return annotationDict


def processFile2():
    for bioNumber in [19]:
        # if bioNumber in [398]:
        #    continue
        # bioNumber = 175
        logMess.log = []
        logMess.counter = -1
        reactionDefinitions, useID, naming = selectReactionDefinitions(
            "BIOMD%010i.xml" % bioNumber
        )
        print(reactionDefinitions, useID)
        # reactionDefinitions = 'reactionDefinitions/reactionDefinition7.json'
        # spEquivalence = 'reactionDefinitions/speciesEquivalence19.json'
        spEquivalence = detectCustomDefinitions(bioNumber)
        print(spEquivalence)
        useID = False
        # reactionDefinitions = 'reactionDefinitions/reactionDefinition9.json'
        outputFile = "complex/output" + str(bioNumber) + ".bngl"
        analyzeFile(
            "XMLExamples/curated/BIOMD%010i.xml" % bioNumber,
            reactionDefinitions,
            useID,
            naming,
            outputFile,
            speciesEquivalence=spEquivalence,
            atomize=True,
            bioGrid=True,
        )

        if len(logMess.log) > 0:
            with open(outputFile + ".log", "w") as f:
                for element in logMess.log:
                    f.write(element + "\n")


def detectCustomDefinitions(bioNumber):
    """
    returns a speciesDefinition<bioNumber>.json fileName if it exist
    for the current bioModels. None otherwise
    """
    directory = "reactionDefinitions"
    onlyfiles = [f for f in listdir("./" + directory)]
    if "speciesEquivalence{0}.json".format(bioNumber) in onlyfiles:
        return "{0}/speciesEquivalence{1}.json".format(directory, bioNumber)
    return None


import pyparsing


def main():
    jsonFiles = [f for f in listdir("./reactionDefinitions") if f[-4:-1] == "jso"]
    jsonFiles.sort()
    parser = OptionParser()
    rulesLength = []
    evaluation = []
    evaluation2 = []
    compartmentLength = []
    parser.add_option(
        "-i",
        "--input",
        dest="input",
        default="XMLExamples/curated/BIOMD0000000272.xml",
        type="string",
        help="The input SBML file in xml format. Default = 'input.xml'",
        metavar="FILE",
    )
    parser.add_option(
        "-o",
        "--output",
        dest="output",
        default="output.bngl",
        type="string",
        help="the output file where we will store our matrix. Default = output.bngl",
        metavar="FILE",
    )

    (options, _) = parser.parse_args()
    # 144
    rdfArray = []
    # classificationArray = []
    # 18, 32, 87, 88, 91, 109, 253, 255, 268, 338, 330
    # normal:51, 353
    # cycles 18, 108, 109, 255, 268, 392
    import progressbar

    progress = progressbar.ProgressBar()
    sbmlFiles = getFiles("XMLExamples/curated", "xml")
    for bioIdx in progress(range(len(sbmlFiles))):
        bioNumber = sbmlFiles[bioIdx]

        # if bioNumber in [81, 151, 175, 205, 212, 223, 235, 255, 326, 328, 347, 370, 404, 428, 430, 431, 443, 444, 452, 453, 465, 474]:
        #    continue
        # bioNumber = 175
        logMess.log = []
        logMess.counter = -1
        # reactionDefinitions, useID, naming = selectReactionDefinitions('BIOMD%010i.xml' %bioNumber)
        # print(reactionDefinitions, useID)
        # reactionDefinitions = 'reactionDefinitions/reactionDefinition7.json'
        # spEquivalence = 'reactionDefinitions/speciesEquivalence19.json'
        # spEquivalence = naming
        # reactionDefinitions = 'reactionDefinitions/reactionDefinition8.json'
        # rlength, reval, reval2, clength, rdf = analyzeFile('XMLExamples/curated/BIOMD%010i.xml' % bioNumber,
        #                                                  reactionDefinitions, False, 'complex/output' + str(bioNumber) + '.bngl',
        #                                                    speciesEquivalence=spEquivalence, atomize=True)
        try:
            fileName = bioNumber.split("/")[-1]
            rlength = reval = reval2 = slength = None
            analysisResults = analyzeFile(
                bioNumber,
                resource_path("config/reactionDefinitions.json"),
                False,
                resource_path("config/namingConventions.json"),
                #'/dev/null',
                "complex2/" + fileName + ".bngl",
                speciesEquivalence=None,
                atomize=True,
                bioGrid=False,
            )
            # rlength, slength, reval, reval2, clength, rdf, _, _ = analysisResults
            # print('++++', bioNumber, rlength, reval, reval2, clength)

        except KeyError:
            print("keyErrorerror--------------", bioNumber)
            continue
        except OverflowError:
            print("overFlowerror--------------", bioNumber)
            continue
        except ValueError:
            print("valueError", bioNumber)
        except pyparsing.ParseException:
            print("pyparsing", bioNumber)
        finally:
            if analysisResults.rlength != None:
                rulesLength.append(
                    {
                        "index": bioNumber,
                        "nreactions": analysisResults.rlength,
                        "atomization": analysisResults.reval,
                        "compression": analysisResults.reval2,
                        "nspecies": analysisResults.slength,
                    }
                )
                compartmentLength.append(analysisResults.clength)
                rdfArray.append(getAnnotationsDict(analysisResults.rdf))

            else:
                rulesLength.append([bioNumber, -1, 0, 0])
                compartmentLength.append(0)
                rdfArray.append({})

            # classificationArray.append({})
    # print(evaluation)
    # print(evaluation2)
    # sortedCurated = [i for i in enumerate(evaluation), key=lambda x:x[1]]
    print([(idx + 1, x) for idx, x in enumerate(rulesLength) if x > 50])
    with open("sortedD.dump", "wb") as f:
        pickle.dump(rulesLength, f)
    with open("annotations.dump", "wb") as f:
        pickle.dump(rdfArray, f)
    # with open('classificationDict.dump', 'wb') as f:
    #    pickle.dump(classificationArray, f)
    """
    plt.hist(rulesLength, bins=[10, 30, 50, 70, 90, 110, 140, 180, 250, 400])
    plt.xlabel('Number of reactions', fontsize=18)
    plt.savefig('lengthDistro.png')
    plt.clf()
    plt.hist(evaluation, bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,
                                0.8, 0.9, 1.0])
    plt.xlabel('Atomization Degree', fontsize=18)
    plt.savefig('ruleifyDistro.png')
    plt.clf()
    plt.hist(evaluation2, bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7,
                                0.8, 0.9, 1.0])
    plt.xlabel('Atomization Degree', fontsize=18)
    plt.savefig('ruleifyDistro2.png')
    plt.clf()
    ev = []
    idx = 1
    for x, y, z in zip(rulesLength, evaluation, compartmentLength):

        if idx in [18, 51, 353, 108, 109, 255, 268, 392]:
            idx+=1

        if x < 15 and y > 0.7 and z>1:
            print('---', idx, x, y)
        idx+=1
    #plt.hist(ev, bins =[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0])
    #plt.xlabel('Atomization Degree', fontsize=18)
    #plt.savefig('ruleifyDistro3.png')
    """


def main2():
    with open("../XMLExamples/curated/BIOMD0000000163.xml", "r") as f:
        st = f.read()
        import StringIO

        stringBuffer = StringIO.StringIO()
        jsonPointer = "reactionDefinitions/speciesEquivalence163.json"
        readFromString(
            st,
            resource_path("config/reactionDefinitions.json"),
            False,
            jsonPointer,
            True,
            stringBuffer,
        )
        print(stringBuffer.getvalue())


def isActivated(statusVector):
    if statusVector[0] != "" or statusVector[1] not in ["", "0"]:
        return True
    return False


def flatStatusVector(statusVector):
    if statusVector[0] != "":
        return "!"
    return statusVector[1]


"""
def xorBox(status1, status2):
    return not(status1 & status2)

def orBox(status1, status2):
    return (status1, status2)

def totalEnumerations(pairList):
    xCoordinate = set()
    yCoordinate = set()
    for element in pairList:
        xCoordinate.add(element[0])
        yCoordinate.add(element[1])
    xCoordinate = list(xCoordinate)
    yCoordinate = list(yCoordinate)
    matrix = np.zeros((len(xCoordinate), len(yCoordinate)))
    for element in pairList:
        matrix[xCoordinate.index(element[0])][yCoordinate.index(element[1])] = 1
    return np.all(np.all(matrix))
"""


def getRelationshipDegree(
    componentPair, statusQueryFunction, comparisonFunction, finalComparison
):
    componentPairRelationshipDict = {}
    for pair in componentPair:
        stats = []
        for state in componentPair[pair]:
            status1 = statusQueryFunction(state[0])
            status2 = statusQueryFunction(state[1])
            comparison = comparisonFunction(status1, status2)
            stats.append(comparison)
        if finalComparison(stats):
            print(pair, componentPair[pair])
        componentPairRelationshipDict[pair] = finalComparison(stats)
    return componentPairRelationshipDict


"""
def createPlot(labelDict):
    #f, ax = plt.subplots(int(math.ceil(len(labelDict)/4)), 4)
    for idx, element in enumerate(labelDict):
        plt.cla()
        tmp = list(set([y for x in labelDict[element] for y in x]))
        xaxis = [tmp.index(x[0]) for x in labelDict[element] if  labelDict[element][x]== True]
        yaxis = [tmp.index(x[1]) for x in labelDict[element] if labelDict[element][x] == True]
        #6print(tmp, xaxis, yaxis)
        plt.scatter(xaxis, yaxis)
        plt.xticks(range(len(tmp)), tmp)
        plt.yticks(range(len(tmp)), tmp)
        plt.title(element)
        #ax[math.floor(idx/4)][idx%4].scatter(xaxis, yaxis)
        #ax[math.floor(idx/4)][idx%4].xticks(range(len(tmp)), tmp)
        #ax[math.floor(idx/4)][idx%4].yticks(range(len(tmp)), tmp)
        #ax[math.floor(idx/4)][idx%4].title(element)
        plt.savefig('{0}.png'.format(element))
        print('{0}.png'.format(element))
"""
"""
def statFiles():

    for bioNumber in [19]:
        reactionDefinitions, useID = selectReactionDefinitions('BIOMD%010i.xml' %bioNumber)
        #speciesEquivalence = None
        speciesEquivalence = 'reactionDefinitions/speciesEquivalence19.json'

        componentPairs =  extractCompartmentStatistics('XMLExamples/curated/BIOMD%010i.xml' % bioNumber, useID, reactionDefinitions, speciesEquivalence)
        #analyze the relationship degree betweeen the components of each molecule

        #in this case we are analyzing for orBoxes, or components
        #that completely exclude each other
        xorBoxDict = {}
        orBoxDict = {}
        for molecule in componentPairs:
            xorBoxDict[molecule] = getRelationshipDegree(componentPairs[molecule], isActivated, xorBox, all)
            #print('----------------------', molecule, '---------'            )
            orBoxDict[molecule] =  getRelationshipDegree(componentPairs[molecule], flatStatusVector, orBox, totalEnumerations)

        #createPlot(orBoxDict)
        box = []
        box.append(xorBoxDict)
        #box.append(orBoxDict)
        with open('orBox{0}.dump'.format(bioNumber), 'wb') as f:
            pickle.dump(box, f)
"""


def processDir(directory, atomize=True):
    from os import listdir
    from os.path import isfile, join

    resultDir = {}
    xmlFiles = [
        f
        for f in listdir("./" + directory)
        if isfile(join("./" + directory, f)) and f.endswith("xml")
    ]
    blackList = [
        175,
        205,
        212,
        223,
        235,
        255,
        328,
        370,
        428,
        430,
        431,
        443,
        444,
        452,
        453,
        465,
    ]

    for xml in xmlFiles:
        # try:
        if (
            xml not in ["MODEL1310110034.xml"]
            and len([x for x in blackList if str(x) in xml]) == 0
        ):
            print(xml)
            try:
                analysisResults = analyzeFile(
                    directory + xml,
                    "reactionDefinitions/reactionDefinition7.json",
                    False,
                    resource_path("config/namingConventions.json"),
                    "/dev/null",
                    speciesEquivalence=None,
                    atomize=True,
                    bioGrid=False,
                )
                resultDir[xml] = [
                    analysisResults.rlength,
                    analysisResults.reval,
                    analysisResults.reval2,
                ]
            except:
                resultDir[xml] = [-1, 0, 0]
    with open("evalResults.dump", "wb") as f:
        pickle.dump(resultDir, f)
        # except:
        # continue'


def processFile3(
    fileName, customDefinitions=None, atomize=True, bioGrid=False, output=None
):
    """
    processes a file. derp.
    """
    logMess.log = []
    logMess.counter = -1
    reactionDefinitions = resource_path("config/reactionDefinitions.json")
    spEquivalence = customDefinitions
    namingConventions = resource_path("config/namingConventions.json")
    # spEquivalence = None
    useID = False
    # reactionDefinitions = 'reactionDefinitions/reactionDefinition9.json'
    # rlength = -1
    # reval = -1
    # reval2 = -1
    if output:
        outputFile = output
    else:
        outputFile = "{0}.bngl".format(fileName)
    analysisResults = analyzeFile(
        fileName,
        reactionDefinitions,
        useID,
        namingConventions,
        outputFile,
        speciesEquivalence=spEquivalence,
        atomize=atomize,
        bioGrid=bioGrid,
    )

    if len(logMess.log) > 0:
        with open(fileName + ".log", "w") as f:
            for element in logMess.log:
                f.write(element + "\n")
    return analysisResults.rlength, analysisResults.reval, analysisResults.reval2


def listFiles(minReactions, directory):
    """
    List of SBML files that meet a given condition
    """
    from os import listdir
    from os.path import isfile, join

    xmlFiles = [
        f
        for f in listdir("./" + directory)
        if isfile(join("./" + directory, f)) and "xml" in f
    ]
    outputList = []
    for xml in xmlFiles:
        print(
            ".",
        )
        reader = libsbml.SBMLReader()
        document = reader.readSBMLFromFile(directory + xml)
        model = document.getModel()
        if model == None:
            continue
        if len(model.getListOfReactions()) > minReactions:
            outputList.append(xml)
    print(len(outputList))


if __name__ == "__main__":
    main2()
