import readBNGXML
import argparse
from collections import defaultdict
from rulifier import stateTransitionDiagram


def defineConsole():
    """
    defines the program console line commands
    """
    parser = argparse.ArgumentParser(description="SBML to BNGL translator")
    parser.add_argument("-f1", "--filename1", type=str, help="base file", required=True)
    parser.add_argument(
        "-f2", "--filename2", type=str, help="comparison file", required=True
    )
    return parser


def evaluateStructureSimilarity(moleculeSet1, moleculeSet2):
    scoreDict = defaultdict(list)
    scoreDict["moleculeSetSize"] = len(moleculeSet1)
    for molecule in moleculeSet1:
        for molecule2 in moleculeSet2:
            if molecule.name == molecule2.name:
                scoreDict["overlap"].append(molecule.name)
                # for now we are considering atomizer models so dont check components other than states
                scoreDict["componentSetSize"].extend(
                    [x.name for x in molecule.components if len(x.states) > 0]
                )
                for component in [x for x in molecule.components if len(x.states) > 0]:
                    for component2 in [
                        x for x in molecule2.components if len(x.states) > 0
                    ]:
                        if component.name == component2.name:
                            scoreDict["componentOverlap"].append(component.name)
    return len(scoreDict["overlap"]), scoreDict["moleculeSetSize"]


def evaluateProcessSimilarity(bnglNamespace, bnglNamespace2):
    stdDictionary1 = stateTransitionDiagram.getContextRequirementsFromNamespace(
        bnglNamespace
    )
    stdDictionary2 = stateTransitionDiagram.getContextRequirementsFromNamespace(
        bnglNamespace2
    )
    intersectingNamespace = [
        x.name
        for x in bnglNamespace["molecules"]
        if x.name in [y.name for y in bnglNamespace2["molecules"]]
    ]

    lowerIntersectionNamespace = [x.lower() for x in intersectingNamespace]
    # extract state coverage
    intersectionSpace = defaultdict(set)
    intersectionSpace2 = defaultdict(set)

    scoreDict = {x: {} for x in intersectingNamespace}
    for element in [x for x in stdDictionary1[0] if x in intersectingNamespace]:
        for state in stdDictionary1[0][element]:
            intersectionSpace[element].add(
                frozenset(x for x in state if x[0] in lowerIntersectionNamespace)
            )

    for element in intersectionSpace:
        scoreDict[element]["file1"] = len(intersectionSpace[element])
        scoreDict[element]["totalSpace"] = 2 ** len(
            next(iter(intersectionSpace[element]))
        )
        print element, scoreDict[element]["totalSpace"], next(
            iter(intersectionSpace[element])
        )

    for element in [x for x in stdDictionary2[0] if x in intersectingNamespace]:
        for state in stdDictionary2[0][element]:
            intersectionSpace2[element].add(
                frozenset(x for x in state if x[0] in lowerIntersectionNamespace)
            )

    for element in intersectionSpace:
        scoreDict[element]["file2"] = len(intersectionSpace2[element])

    for element in intersectionSpace:
        scoreDict[element]["intersection"] = [
            len(intersectionSpace[element] - intersectionSpace2[element]),
            len(intersectionSpace2[element] - intersectionSpace[element]),
        ]
        scoreDict[element]["score"] = (
            1
            - scoreDict[element]["intersection"][0] * 1.0 / scoreDict[element]["file1"]
        )
        scoreDict[element]["score2"] = (
            1
            - scoreDict[element]["intersection"][1] * 1.0 / scoreDict[element]["file2"]
        )

    return scoreDict


def evaluateSimilarity(bnglNamespace, bnglNamespace2):
    similarity = {}
    similarity["structure"] = evaluateStructureSimilarity(
        bnglNamespace["molecules"], bnglNamespace2["molecules"]
    )
    similarity["process"] = evaluateProcessSimilarity(bnglNamespace, bnglNamespace2)
    return similarity


if __name__ == "__main__":
    parser = defineConsole()
    namespace = parser.parse_args()

    bnglNamespace = readBNGXML.parseFullXML(namespace.filename1)
    bnglNamespace2 = readBNGXML.parseFullXML(namespace.filename2)
    evaluateSimilarity(bnglNamespace, bnglNamespace2)
