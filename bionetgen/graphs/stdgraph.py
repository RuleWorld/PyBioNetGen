from bionetgen.core.utils.logging import BNGLogger
from bionetgen.modelapi import bngmodel
import networkx as nx

from collections import defaultdict, Counter
from collections.abc import MutableSet


def extractMolecules(action, site1, site2, chemicalArray, differentiateDimers=False):
    """
    this method goes through the chemicals in a given array 'chemicalArray'
    and extracts its atomic patterns into two arrays:
        those elements that are contained in [site1,site2] will be put in the
        reactionCenter set. The rest will    be placed in the context set.
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


class OrderedEdgeSet(MutableSet):
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
        if isinstance(other, OrderedEdgeSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)


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
    edgeList = defaultdict(OrderedEdgeSet)
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
                        if element.split("(")[0].split("%")[0] not in sourceCounter:
                            sourceCounter[
                                element.split("(")[0].split("%")[0]
                            ] = Counter()
                            for component in moleculeDict[
                                element.split("(")[0].split("%")[0]
                            ]:
                                sourceCounter[element.split("(")[0].split("%")[0]][
                                    component
                                ] = 0
                        if isActive(element.split("(")[1][:-1]):
                            componentName = (
                                element.split("(")[1][:-1].split("~")[0].split("!")[0]
                            )
                            tmpSourceCounter[element.split("(")[0].split("%")[0]][
                                componentName
                            ] += centerUnit[species]
            else:
                for species in centerUnit:
                    for element in species.split("."):
                        if element.split("(")[0].split("%")[0] not in sourceCounter:
                            sourceCounter[
                                element.split("(")[0].split("%")[0]
                            ] = Counter()
                            for component in moleculeDict[
                                element.split("(")[0].split("%")[0]
                            ]:
                                sourceCounter[element.split("(")[0].split("%")[0]][
                                    component
                                ] = 0
                        if isActive(element.split("(")[1][:-1]):
                            componentName = (
                                element.split("(")[1][:-1].split("~")[0].split("!")[0]
                            )
                            sourceCounter[element.split("(")[0].split("%")[0]][
                                componentName
                            ] += centerUnit[species]
                    tmpContext[species] = contextUnit
                flag = False
            for species in productUnit:
                for element in species.split("."):
                    if element.split("(")[0].split("%")[0] not in destinationCounter:
                        destinationCounter[
                            element.split("(")[0].split("%")[0]
                        ] = Counter()
                        for component in moleculeDict[
                            element.split("(")[0].split("%")[0]
                        ]:
                            destinationCounter[element.split("(")[0].split("%")[0]][
                                component
                            ] = 0

                    if isActive(element.split("(")[1][:-1]):
                        componentName = (
                            element.split("(")[1][:-1].split("~")[0].split("!")[0]
                        )
                        destinationCounter[element.split("(")[0].split("%")[0]][
                            componentName
                        ] += productUnit[species]
        # add the first context unit
        if len(tmpContext) > 0:
            finalContext = tmpContext[tmpContext.keys()[0]]
            for idx in range(1, len(tmpContext.keys())):
                finalContext[tmpContext.keys()[idx]] -= 1
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


def getContextRequirementsFromNamespace(namespace, excludeReverse=False):
    (
        label,
        center,
        context,
        product,
        atomicArray,
        actions,
        doubleAction,
    ) = extractCenterContext(namespace["rules"], excludeReverse=excludeReverse)
    return getStateTransitionDiagram(
        label,
        center,
        product,
        context,
        actions,
        namespace["molecules"],
        namespace["rules"],
        namespace["parameters"],
    )


#####


class STDGraph:
    def __init__(self, inp, app=None):
        self.app = app
        self.logger = BNGLogger(app=self.app)
        self.logger.info(  # debug
            "Setting up STDGraph object", loc=f"{__file__} : STDGraph.__init__()"
        )
        if isinstance(inp, str):
            if inp.endswith(".bngl") or inp.endswith(".xml"):
                self.logger.info(  # debug
                    f"Loading model from file {inp}",
                    loc=f"{__file__} : STDGraph.__init__()",
                )
                self.model = bngmodel(inp)
            else:
                self.logger.info(  # error
                    f"Input {inp} is not recognized for STD graph generation",
                    loc=f"{__file__} : STDGraph.__init__()",
                )
        elif isinstance(inp, bngmodel):
            # we got the model directly
            self.model = bngmodel
        else:
            self.logger.info(  # error
                f"Input {inp} is not recognized for STD graph generation",
                loc=f"{__file__} : STDGraph.__init__()",
            )
        self.ID_counter = 0

    def getID(self):
        curr_id = self.ID_counter
        self.ID_counter += 1
        return curr_id

    def generateSTDGML(self, simplifiedText=False):
        nodeList, edgeList = self.getContextRequirements(excludeReverse=False)
        graph = self.generateSTD(nodeList, edgeList, simplifiedText)
        return graph

    def getContextRequirements(
        self, collapse=True, motifFlag=False, excludeReverse=False
    ):
        """
        Receives a BNG-XML file and returns the contextual dependencies implied by this file
        """
        # molecules, rules, parameters = readBNGXML.parseXML(inputfile)

        moleculeStateMatrix = {}
        (
            label,
            center,
            context,
            product,
            atomicArray,
            actions,
            doubleAction,
        ) = self.extractCenterContext(self.model.rules, excludeReverse=excludeReverse)
        return getStateTransitionDiagram(
            label, center, product, context, actions, molecules, rules, parameters
        )

    def extractCenterContext(self, excludeReverse=False):
        transformationCenter = []
        transformationContext = []
        transformationProduct = []
        atomicArray = []
        actionNames = []
        label = []
        doubleModificationRules = []
        for idx, rule in enumerate(self.model.rules):
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

    def extractTransformations(self, rules, differentiateDimers=False):
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
        for rule, _, reationRate, reactionSymbol in rules:
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

    #####
    def createNode(self, graph, name, graphicsDict, labelGraphicsDict, isGroup, gid):
        idNumber = self.getID()
        if isGroup:
            if gid:
                graph.add_node(
                    name,
                    graphics=graphicsDict,
                    LabelGraphics=labelGraphicsDict,
                    isGroup=isGroup,
                    gid=gid,
                    id=idNumber,
                )
            else:
                graph.add_node(
                    name,
                    graphics=graphicsDict,
                    LabelGraphics=labelGraphicsDict,
                    isGroup=isGroup,
                    id=idNumber,
                )
        else:
            graph.add_node(
                name,
                graphics=graphicsDict,
                LabelGraphics=labelGraphicsDict,
                gid=gid,
                id=idNumber,
            )
        return idNumber

    def createBitNode(self, graph, molecule, nodeList, simplifiedText):
        """
        creates the bit nodes
        """
        gridDict = {
            1: 1,
            2: 2,
            3: 3,
            4: 2,
            5: 3,
            6: 3,
            7: 4,
            8: 4,
            9: 3,
            10: 5,
            11: 4,
            12: 4,
            13: 5,
            14: 5,
            15: 5,
            16: 4,
            17: 5,
            18: 4,
            19: 5,
            20: 5,
        }

        for node in nodeList[molecule]:
            componentLegend = ""
            nodeName = ""
            nodeId = []
            for idx, bit in enumerate(node):
                componentLegend += bit[0]
                if bit[1]:
                    if simplifiedText:
                        nodeName += "o"
                    else:
                        nodeName += "\u25CF "
                    nodeId.append(bit[0])
                else:
                    if simplifiedText:
                        nodeName += "x"
                    else:
                        nodeName += "\u25CB "
                    # nodeName += u"\u00B7 "
                if (idx + 1) % gridDict[len(node)] == 0 and idx + 1 != len(node):
                    nodeName.strip(" ")
                    nodeName += "\n"
                    componentLegend += "\n"
                else:
                    componentLegend += "/"
            self.createNode(
                graph,
                "{0}_{1}".format(molecule, "/".join(nodeId)),
                {"type": "roundrectangle"},
                {"text": nodeName},
                0,
                graph.node[molecule]["id"],
            )
        self.createNode(
            graph,
            "{0}_legend".format(molecule),
            {},
            {"text": componentLegend, "fontSize": 20},
            0,
            graph.node[molecule]["id"],
        )

    def createBitEdge(self, graph, molecule, edge, edgeList):
        nodeId0 = [x[0] for x in edge[0] if x[1]]
        nodeId1 = [x[0] for x in edge[1] if x[1]]
        bidirectional = (edge[1], edge[0]) in edgeList[molecule]
        if (
            "{0}_{1}".format(molecule, "/".join(nodeId1)),
            "{0}_{1}".format(molecule, "/".join(nodeId0)),
        ) not in graph.edges():
            if bidirectional:
                graph.add_edge(
                    "{0}_{1}".format(molecule, "/".join(nodeId0)),
                    "{0}_{1}".format(molecule, "/".join(nodeId1)),
                    graphics={
                        "fill": "#000000",
                        "sourceArrow": "standard",
                        "targetArrow": "standard",
                    },
                )

            else:
                graph.add_edge(
                    "{0}_{1}".format(molecule, "/".join(nodeId0)),
                    "{0}_{1}".format(molecule, "/".join(nodeId1)),
                    graphics={"fill": "#000000", "targetArrow": "standard"},
                )

    def createPDLabelNode(self, graph, molecule, nodeList):
        globalLabelDict = {}
        for node in nodeList[molecule]:
            localNodeName = "{0}_{1}".format(
                molecule, "/".join([x[0] for x in node if x[1]])
            )
            labelDict = []
            anchorArray = ["c", "t", "tl", "tr", "l", "r", "bl", "b", "br"]
            for anchor, bit in zip(anchorArray, node):
                localLabelDict = {}

                # localLabelDict['outline'] = '#FFFFFF'
                localLabelDict["text"] = str(bit[0])
                localLabelDict["fill"] = "#FF88FF" if bit[1] else "#FFFFFF"
                localLabelDict["fontSize"] = 24
                localLabelDict["anchor"] = anchor

                labelDict.append(localLabelDict)

            self.createNode(
                graph,
                localNodeName,
                {"type": "roundrectangle", "fill": "#FFFFFF", "w": 270, "h": 140},
                {},
                0,
                graph.node[molecule]["id"],
            )
            globalLabelDict[localNodeName] = labelDict
        return globalLabelDict

    def createPDGraphNode(self, graph, molecule, nodeList):
        for node in nodeList[molecule]:
            localNodeName = "{0}_{1}".format(
                molecule, "/".join([x[0] for x in node if x[1]])
            )
            self.createNode(
                graph,
                localNodeName,
                {"type": "roundrectangle", "fill": "#FFFFFF"},
                {"text": " "},
                1,
                graph.node[molecule]["id"],
            )

            localNodeid = graph.node[localNodeName]["id"]
            subNodeId = []
            for bit in node:
                if bit[1]:
                    nodecolor = "#FF88FF"
                    self.createNode(
                        graph,
                        "{0}_{1}".format(localNodeid, bit[0]),
                        {"type": "roundrectangle", "fill": nodecolor},
                        {"text": bit[0]},
                        0,
                        localNodeid,
                    )

                else:
                    nodecolor = "#FFFFFF"
                    self.createNode(
                        graph,
                        "{0}_{1}".format(localNodeid, bit[0]),
                        {"type": "roundrectangle", "fill": nodecolor},
                        {"text": bit[0]},
                        0,
                        localNodeid,
                    )
                subNodeId.append("{0}_{1}".format(localNodeid, bit[0]))

            for idx in range(0, len(subNodeId) - 1):
                graph.add_edge(
                    subNodeId[idx],
                    subNodeId[idx + 1],
                    graphics={"fill": "#CCCCFF", "style": "dashed"},
                )

            # for idx in range(0, len(subNodeId)/2):
            #    graph.add_edge(subNodeId[idx], subNodeId[idx+len(subNodeId)/2], graphics={'fill': '#CCCCFF', 'style': 'dashed'})

    def createPDEdge(self, graph, molecule, edge, edgeList):
        nodeId0 = [x[0] for x in edge[0] if x[1]]
        nodeId1 = [x[0] for x in edge[1] if x[1]]

        bidirectionalArray = [
            x for x in edgeList[molecule] if (edge[1], edge[0]) == (x[0], x[1])
        ]

        bidirectional = len(bidirectionalArray) > 0

        if (
            "{0}_{1}".format(molecule, "/".join(nodeId1)),
            "{0}_{1}".format(molecule, "/".join(nodeId0)),
        ) not in graph.edges():
            transDict = {False: "^", True: ""}
            processNodeName = "{0}_{1}_{2}_edge".format(
                molecule, "/".join(nodeId0), "/".join(nodeId1)
            )
            if "reverse" in edge[2]:
                difference = set(edge[0]) - set(edge[1])
            else:
                difference = set(edge[1]) - set(edge[0])

            # if not bidirectional:
            #    differenceText = ['{1}{0}'.format(x[0],transDict[x[1]]) for x in difference]
            # else:
            #    differenceText = ['{0}'.format(x[0]) for x in difference]

            differencePositive = [x[0] for x in difference if x[1]]
            differenceNegative = [x[0] for x in difference if not x[1]]

            if bidirectional:
                if "reverse" in edge[2]:
                    differenceText = bidirectionalArray[0][3] + ", " + edge[3]
                else:
                    differenceText = edge[3] + ", " + bidirectionalArray[0][3]
            else:
                differenceText = edge[3]

            # differenceText = edge[2].strip('_reverse_')
            differenceText += "\n===\n"
            differenceText = ""

            # if bidirectional and len(differencePositive) < len(differenceNegative):
            #    differencePositive, differenceNegative = differenceNegative, differencePositive
            if len(differencePositive) > 0 and len(differenceNegative) > 0:
                differenceText += (
                    ", ".join(differencePositive)
                    + "\n___\n"
                    + ", ".join(["^{0}".format(x) for x in differenceNegative])
                )
            else:
                differenceText += ", ".join(differencePositive) + ", ".join(
                    ["^{0}".format(x) for x in differenceNegative]
                )

            # creates the process nodes with text 'differenceText'
            self.createNode(
                graph,
                processNodeName,
                {"type": "rectangle", "fill": "#FFFFFF"},
                {"text": differenceText, "fontStyle": "bold", "fontSize": 20},
                0,
                graph.node[molecule]["id"],
            )
            if bidirectional:
                graph.add_edge(
                    "{0}_{1}".format(molecule, "/".join(nodeId0)),
                    processNodeName,
                    graphics={"fill": "#000000", "sourceArrow": "standard", "width": 3},
                )
                graph.add_edge(
                    processNodeName,
                    "{0}_{1}".format(molecule, "/".join(nodeId1)),
                    graphics={"fill": "#000000", "targetArrow": "standard", "width": 3},
                )
            else:
                graph.add_edge(
                    "{0}_{1}".format(molecule, "/".join(nodeId0)),
                    processNodeName,
                    graphics={"fill": "#000000", "width": 3},
                )
                graph.add_edge(
                    processNodeName,
                    "{0}_{1}".format(molecule, "/".join(nodeId1)),
                    graphics={"fill": "#000000", "targetArrow": "standard", "width": 3},
                )
        return bidirectional

    def generateSTD(self, nodeList, edgeList, simplifiedText=False):
        graph = nx.DiGraph()
        globalLabelDict = {}
        for molecule in nodeList:
            self.createNode(
                graph,
                molecule,
                {"type": "roundrectangle", "fill": "#FFFFFF"},
                {
                    "fontSize": 24,
                    "fontStyle": "bold",
                    "alignment": "right",
                    "autoSizePolicy": "node_size",
                },
                1,
                0,
            )

            # globalLabelDict.update(createPDLabelNode(graph, molecule, nodeList))
            self.createBitNode(graph, molecule, nodeList, simplifiedText)

        for molecule in nodeList:

            bidirectionalList = []
            cedgeList = list(edgeList[molecule])
            for edge in cedgeList:
                if "_reverse" in edge[2]:
                    continue
                if list([edge[0], edge[1]]) not in bidirectionalList:

                    bidirectional = self.createPDEdge(graph, molecule, edge, edgeList)
                if bidirectional:
                    bidirectionalList.append([edge[1], edge[0]])

        return graph

    def outputGraph(self, graph, fileName):
        nx.write_graphml(graph, fileName)


if __name__ == "__main__":
    import sys

    i = sys.argv[1]
    g = STDGraph(i)
    import IPython

    IPython.embed()
    # gml = g.generateSTDGML()


# if __name__ == "__main__":

#     parser = defineConsole()
#     namespace = parser.parse_args()
#     inputFile = namespace.input

#     graph = generateSTDGML(inputFile)
#     nx.write_gml(graph, inputFile + "_std.gml")
#     # print gmlgraph[0:400]
#     # nxgml = nx.parse_gml(gmlgraph)
#     # import gml2cyjson
#     # gmlgraph = nx.parse_gml(gmlgraph)
#     # gml2cyjson.gml2cyjson(gmlgraph,'std')
#     # nodeList, edgeList = std.getContextRequirements(inputFile, excludeReverse=True)
#     # graph = generateSTD(nodeList, edgeList)
#     # outputGraph(graph, '{0}_std.gml'.format(namespace.input), {})
