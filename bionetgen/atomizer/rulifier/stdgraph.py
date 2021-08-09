import networkx as nx
import stateTransitionDiagram as std
import argparse
import math
import StringIO


def ato_write_gml(graph, fileName, labelGraphics):
    def writeDict(gml, key, label, contents, space, labelGraphics=None):
        gml.write("{1}{0} [\n".format(key, space))
        for subKey in contents:
            if type(contents[subKey]) in [str]:
                gml.write('{2}\t{0} "{1}"\n'.format(subKey, contents[subKey], space))
            elif type(contents[subKey]) in [int]:
                gml.write("{2}\t{0} {1}\n".format(subKey, contents[subKey], space))
            elif type(contents[subKey]) in [dict]:
                writeDict(gml, subKey, subKey, contents[subKey], space + "\t")
            if labelGraphics and label in labelGraphics:
                for labelInstance in labelGraphics[label]:
                    writeDict(
                        gml,
                        "LabelGraphics",
                        "LabelGraphics",
                        labelInstance,
                        space + "\t",
                    )
        gml.write("{0}]\n".format(space))

    gml = StringIO.StringIO()
    gml.write("graph [\n")
    gml.write("\tdirected 1\n")
    for node in graph.node:

        writeDict(gml, "node", node, graph.node[node], "\t", labelGraphics)

    flag = False
    for x in nx.generate_gml(graph):
        if "edge" in x and not flag:
            flag = True
        if flag:
            gml.write(x + "\n")

    # gml.write(']\n')
    with open(fileName, "w") as f:
        f.write(gml.getvalue())
    nx.read_gml(fileName)


def defineConsole():
    """
    defines the program console line commands
    """
    parser = argparse.ArgumentParser(description="SBML to BNGL translator")
    parser.add_argument("-i", "--input", type=str, help="settings file", required=True)
    return parser


def getCounter():
    if not hasattr(getCounter, "counter"):
        getCounter.counter = 0

    getCounter.counter += 1
    return getCounter.counter


def createNode(graph, name, graphicsDict, labelGraphicsDict, isGroup, gid):
    idNumber = getCounter()
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


def createBitNode(graph, molecule, nodeList, simplifiedText):
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
        nodeName = u""
        nodeId = []
        for idx, bit in enumerate(node):
            componentLegend += bit[0]
            if bit[1]:
                if simplifiedText:
                    nodeName += "o"
                else:
                    nodeName += u"\u25CF "
                nodeId.append(bit[0])
            else:
                if simplifiedText:
                    nodeName += "x"
                else:
                    nodeName += u"\u25CB "
                # nodeName += u"\u00B7 "
            if (idx + 1) % gridDict[len(node)] == 0 and idx + 1 != len(node):
                nodeName.strip(" ")
                nodeName += "\n"
                componentLegend += "\n"
            else:
                componentLegend += "/"
        createNode(
            graph,
            "{0}_{1}".format(molecule, "/".join(nodeId)),
            {"type": "roundrectangle"},
            {"text": nodeName},
            0,
            graph.node[molecule]["id"],
        )
    createNode(
        graph,
        "{0}_legend".format(molecule),
        {},
        {"text": componentLegend, "fontSize": 20},
        0,
        graph.node[molecule]["id"],
    )


def createBitEdge(graph, molecule, edge):
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


def createPDLabelNode(graph, molecule, nodeList):
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

        createNode(
            graph,
            localNodeName,
            {"type": "roundrectangle", "fill": "#FFFFFF", "w": 270, "h": 140},
            {},
            0,
            graph.node[molecule]["id"],
        )
        globalLabelDict[localNodeName] = labelDict
    return globalLabelDict


def createPDGraphNode(graph, molecule, nodeList):
    for node in nodeList[molecule]:
        localNodeName = "{0}_{1}".format(
            molecule, "/".join([x[0] for x in node if x[1]])
        )
        createNode(
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
                createNode(
                    graph,
                    "{0}_{1}".format(localNodeid, bit[0]),
                    {"type": "roundrectangle", "fill": nodecolor},
                    {"text": bit[0]},
                    0,
                    localNodeid,
                )

            else:
                nodecolor = "#FFFFFF"
                createNode(
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


def createPDEdge(graph, molecule, edge, edgeList):
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
        createNode(
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


def generateSTD(nodeList, edgeList, simplifiedText=False):
    graph = nx.DiGraph()
    globalLabelDict = {}
    for molecule in nodeList:
        createNode(
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
        createBitNode(graph, molecule, nodeList, simplifiedText)

    for molecule in nodeList:

        bidirectionalList = []
        cedgeList = list(edgeList[molecule])
        for edge in cedgeList:
            if "_reverse" in edge[2]:
                continue
            if list([edge[0], edge[1]]) not in bidirectionalList:

                bidirectional = createPDEdge(graph, molecule, edge, edgeList)
            if bidirectional:
                bidirectionalList.append([edge[1], edge[0]])

    return graph


def outputGraph(graph, fileName, labelDict):
    nx.write_gml(graph, fileName)
    # ato_write_gml(graph, fileName, labelDict)


import codecs


def generateSTDGML(inputFile, simplifiedText=False):
    nodeList, edgeList = std.getContextRequirements(inputFile, excludeReverse=False)
    graph = generateSTD(nodeList, edgeList, simplifiedText)
    # graph = nx.convert_node_labels_to_integers(graph)
    # gml = nx.generate_gml(graph)
    # print graph
    # nx.write_gml(graph,inputFile+'_std.gml')
    # with open(inputFile+'_std.gml','r') as f:
    #    gml = f.read()
    # gml = codecs.open(inputFile + '.gml', 'r','utf-8')
    # gml = ''.join(gml)
    # return gml.read()
    # return graph
    # return ''.join(gml)
    # gmlstr =  ''.join(gml)
    # gmlstr = gmlstr.encode('utf-8')
    return graph


if __name__ == "__main__":

    parser = defineConsole()
    namespace = parser.parse_args()
    inputFile = namespace.input

    graph = generateSTDGML(inputFile)
    nx.write_gml(graph, inputFile + "_std.gml")
    # print gmlgraph[0:400]
    # nxgml = nx.parse_gml(gmlgraph)
    # import gml2cyjson
    # gmlgraph = nx.parse_gml(gmlgraph)
    # gml2cyjson.gml2cyjson(gmlgraph,'std')
    # nodeList, edgeList = std.getContextRequirements(inputFile, excludeReverse=True)
    # graph = generateSTD(nodeList, edgeList)
    # outputGraph(graph, '{0}_std.gml'.format(namespace.input), {})
