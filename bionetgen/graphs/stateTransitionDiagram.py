from bionetgen.atomizer.utils import readBNGXML
from collections import defaultdict, Counter
from collections.abc import MutableSet
import IPython, sys

# Edge set definition
class OrderedSet(MutableSet):
    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, prev, next = self.map.pop(key)
            prev[2] = next
            next[1] = prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError("set is empty")
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return "%s()" % (self.__class__.__name__,)
        return "%s(%r)" % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


## extractAtomic.py starts here


def extractMolecules(action, site1, site2, chemicalArray, differentiateDimers=False):
    """
    this method goes through the chemicals in a given array 'chemicalArray'
    and extracts its atomic patterns into two arrays:
        those elements that are contained in [site1,site2] will be put in the
        reactionCenter set. The rest will be placed in the context set.
        The entire system will be put into the atomicPatterns dictionary

    Keyword arguments:
        site1,site2 -- where the action takes place
        chemicalArray -- the list of species we will be extracting atomic patters
        from
    """
    atomicPatterns = {}
    reactionCenter = set()
    context = set()
    reactionCenterC = Counter()
    contextC = Counter()
    for reactant in chemicalArray:
        ta, tr, tc = reactant.extractAtomicPatterns(
            action, site1, site2, differentiateDimers
        )
        atomicPatterns.update(ta)
        for element in tr:
            reactionCenter.add(element)

        for element in tc:
            context.add(element)

        reactionCenterC.update(tr)
        contextC.update(tc)

    return (atomicPatterns, reactionCenterC, contextC)


def solveWildcards(atomicArray):
    """
    When you have a wildcard '+' as a bond configuration, this method allows you
    to go through the list of atomic elements and find which patterns the '+'
    can potentially resolve to
    """
    standinArray = {}
    for wildcard in [x for x in atomicArray if "+" in x]:
        for atomic in [
            x for x in atomicArray if "+" not in x and len(atomicArray[x].molecules) > 1
        ]:
            if atomicArray[wildcard].molecules[0].name in [
                x.name for x in atomicArray[atomic].molecules
            ]:
                if wildcard not in standinArray:
                    standinArray[wildcard] = []
                standinArray[wildcard].append(atomicArray[atomic])

    atomicArray.update(standinArray)


def getMapping(mapp, site):
    for mapping in mapp:
        if site in mapping:
            return [x for x in mapping if x != site][0]


def extractTransformations(rules, differentiateDimers=False):
    """
    goes through the list of rules and extracts its reactioncenter,context and product
    atomic patterns per transformation action
    """
    atomicArray = {}
    transformationCenter = []
    transformationContext = []
    productElements = []
    actionName = []
    index = 0
    label = []
    for rule, _, reactionRate, reactionSymbol in rules:
        index += 1
        for action in rule.actions:
            atomic, reactionCenter, context = extractMolecules(
                action.action,
                action.site1,
                action.site2,
                rule.reactants,
                differentiateDimers,
            )
            transformationCenter.append(reactionCenter)
            transformationContext.append(context)
            atomicArray.update(atomic)
            productSites = [
                getMapping(rule.mapping, action.site1),
                getMapping(rule.mapping, action.site2),
            ]
            atomic, rc, _ = extractMolecules(
                action.action,
                productSites[0],
                productSites[1],
                rule.products,
                differentiateDimers,
            )
            productElements.append(rc)
            atomicArray.update(atomic)
            actionName.append("%i-%s" % (index, action.action))
            r = "+".join([str(x) for x in rule.reactants])
            p = "+".join([str(x) for x in rule.products])
            label.append("->".join([r, p, "%i-%s" % (index, action.action)]))

    solveWildcards(atomicArray)
    return (
        atomicArray,
        transformationCenter,
        transformationContext,
        productElements,
        actionName,
        label,
    )


## extractAtomic.py ends here


def getStateTransitionDiagram(
    labels, centers, products, contexts, actions, molecules, rules, parameters
):
    def isActive(state):
        return "!" in state or ("~" in state and "~0" not in state)

    moleculeDict = defaultdict(list)

    for molecule in molecules:
        for component in molecule.components:
            moleculeDict[molecule.name].append(component.name)
    nodeList = defaultdict(set)
    edgeList = defaultdict(OrderedSet)
    for label, center, product, context, action, rule in zip(
        labels, centers, products, contexts, actions, rules
    ):
        sourceCounter = {}
        destinationCounter = {}

        tmpSourceCounter = defaultdict(Counter)
        tmpContext = {}
        flag = True

        for centerUnit, productUnit, actionUnit, contextUnit in zip(
            center, product, action, context
        ):
            # create a node label based on reactant + context/ product + context
            if "ChangeCompartment" in actionUnit:
                continue
            if not flag:
                for species in centerUnit:
                    for element in species.split("."):
                        save_this_ffs = element.split("(")[0].split("%")[0]
                        if save_this_ffs not in sourceCounter:
                            sourceCounter[save_this_ffs] = Counter()
                            for component in moleculeDict[save_this_ffs]:
                                sourceCounter[save_this_ffs][component] = 0
                        if isActive(element.split("(")[1][:-1]):
                            componentName = (
                                element.split("(")[1][:-1].split("~")[0].split("!")[0]
                            )
                            tmpSourceCounter[save_this_ffs][
                                componentName
                            ] += centerUnit[species]
            else:
                for species in centerUnit:
                    for element in species.split("."):
                        save_this_ffs = element.split("(")[0].split("%")[0]
                        if save_this_ffs not in sourceCounter:
                            sourceCounter[save_this_ffs] = Counter()
                            for component in moleculeDict[save_this_ffs]:
                                sourceCounter[save_this_ffs][component] = 0
                        if isActive(element.split("(")[1][:-1]):
                            componentName = (
                                element.split("(")[1][:-1].split("~")[0].split("!")[0]
                            )
                            sourceCounter[save_this_ffs][componentName] += centerUnit[
                                species
                            ]
                    tmpContext[species] = contextUnit
                flag = False
            for species in productUnit:
                for element in species.split("."):
                    save_this_ffs = element.split("(")[0].split("%")[0]
                    if save_this_ffs not in destinationCounter:
                        destinationCounter[save_this_ffs] = Counter()
                        for component in moleculeDict[save_this_ffs]:
                            destinationCounter[save_this_ffs][component] = 0

                    if isActive(element.split("(")[1][:-1]):
                        componentName = (
                            element.split("(")[1][:-1].split("~")[0].split("!")[0]
                        )
                        destinationCounter[save_this_ffs][componentName] += productUnit[
                            species
                        ]
        # add the first context unit
        if len(tmpContext) > 0:
            key = list(tmpContext.keys())[0]
            finalContext = tmpContext[key]
            for idx in range(1, len(tmpContext.keys())):
                tmp_key = list(tmpContext.keys())[idx]
                finalContext[tmp_key] -= 1
        else:
            finalContext = {}
        for species in finalContext:
            # for speciesUnit in tmpContext:
            #    for species in tmpContext[speciesUnit]:
            for element in species.split("."):
                if isActive(element.split("(")[1][:-1]):

                    if element.split("(")[0].split("%")[0] in sourceCounter:
                        componentName = (
                            element.split("(")[1][:-1].split("~")[0].split("!")[0]
                        )

                        sourceCounter[element.split("(")[0].split("%")[0]][
                            componentName
                        ] += finalContext[species]
                        destinationCounter[element.split("(")[0].split("%")[0]][
                            componentName
                        ] += finalContext[species]

        for element in tmpSourceCounter:
            destinationCounter[element].subtract(tmpSourceCounter[element])
        for molecule in sourceCounter:

            if molecule in destinationCounter:
                localMoleculeCounter = Counter(moleculeDict[molecule])
                # get total list of nodes. this is important because of symmetric components

                # sourceTuple = tuple(sorted([(x[0], x[1] > 0) for x in sourceCounter[molecule].items()], key=lambda x: x[0]))
                # destinationTuple = tuple(sorted([(x[0], x[1] > 0) for x in destinationCounter[molecule].items()], key=lambda x: x[0]))

                sourceTuple = []
                for x in sourceCounter[molecule].items():
                    sourceTuple.append((x[0], x[1] > 0))
                    for idx in range(1, localMoleculeCounter[x[0]]):
                        sourceTuple.append(
                            ("{0}-{1}".format(x[0], idx + 1), x[1] > idx)
                        )
                sourceTuple = tuple(sorted(sourceTuple, key=lambda x: x[0]))

                destinationTuple = []
                for x in destinationCounter[molecule].items():
                    destinationTuple.append((x[0], x[1] > 0))
                    for idx in range(1, localMoleculeCounter[x[0]]):
                        destinationTuple.append(
                            ("{0}-{1}".format(x[0], idx + 1), x[1] > idx)
                        )
                destinationTuple = tuple(sorted(destinationTuple, key=lambda x: x[0]))

                # sourceTuple = tuple(sorted([x[0] for x in sourceCounter[molecule].items()]))
                # destinationTuple = tuple(sorted([x[0] for x in destinationCounter[molecule].items() if x[1]> 0]))

                nodeList[molecule].add(sourceTuple)
                nodeList[molecule].add(destinationTuple)
                parameterList = [
                    parameters[x] if x in parameters else x for x in rule[0].rates
                ]
                edgeList[molecule].add(
                    (sourceTuple, destinationTuple, label, ",".join(parameterList))
                )
        # find the intersection context set
    return nodeList, edgeList


def extractCenterContext(rules, excludeReverse=False):
    transformationCenter = []
    transformationContext = []
    transformationProduct = []
    atomicArray = []
    actionNames = []
    label = []
    doubleModificationRules = []
    for idx, rule in enumerate(rules):
        (
            tatomicArray,
            ttransformationCenter,
            ttransformationContext,
            tproductElements,
            tactionNames,
            tlabelArray,
        ) = extractTransformations([rule], True)
        if excludeReverse and "_reverse_" in rule[0].label:
            continue
        label.append(rule[0].label)

        if len([x for x in tactionNames if "ChangeCompartment" not in x]) > 1:
            doubleModificationRules.append(rule[0].label)
        transformationCenter.append(ttransformationCenter)
        transformationContext.append(ttransformationContext)

        actionNames.append(tactionNames)
        atomicArray.append(tatomicArray)
        transformationProduct.append(tproductElements)
    return (
        label,
        transformationCenter,
        transformationContext,
        transformationProduct,
        atomicArray,
        actionNames,
        doubleModificationRules,
    )


def getContextRequirements(
    inputfile, collapse=True, motifFlag=False, excludeReverse=False
):
    """
    Receives a BNG-XML file and returns the contextual dependencies implied by this file
    """
    molecules, rules, parameters = readBNGXML.parseXML(inputfile)
    # import IPython;IPython.embed()

    moleculeStateMatrix = {}
    (
        label,
        center,
        context,
        product,
        atomicArray,
        actions,
        doubleAction,
    ) = extractCenterContext(rules, excludeReverse=excludeReverse)
    return getStateTransitionDiagram(
        label, center, product, context, actions, molecules, rules, parameters
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SBML to BNGL translator")
    parser.add_argument("-i", "--input", type=str, help="settings file", required=True)
    namespace = parser.parse_args()
    inputFile = namespace.input

    import bionetgen

    global model
    model = bionetgen.bngmodel(inputFile)

    stateDictionary = getContextRequirements(inputFile, collapse=True, motifFlag=True)

    IPython.embed()
