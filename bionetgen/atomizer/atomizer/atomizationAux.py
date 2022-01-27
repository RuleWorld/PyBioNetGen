from pyparsing import Word, Suppress, Optional, alphanums, Group, ZeroOrMore
from bionetgen.atomizer.utils.util import pmemoize as memoize


class CycleError(Exception):

    """Exception raised for errors in the input.

    Attributes:
        expr -- input expression in which the error occurred
        msg  -- explanation of the error
    """

    def __init__(self, memory):
        self.memory = memory


def addToDependencyGraph(dependencyGraph, label, value):
    if label not in dependencyGraph:
        dependencyGraph[label] = []
    if value not in dependencyGraph[label] and value != []:
        dependencyGraph[label].append(value)


def getURIFromSBML(moleculeName, parser, filterString=None):
    """
    filters a list of URI's so that we get only filterString  ID's
    """
    annotationList = []
    if parser:
        annotations = parser.getSpeciesAnnotation()
        if annotations[moleculeName]:
            for annotation in annotations[moleculeName]:
                annotationList.extend(getAnnotations(annotation))
    if filterString:
        annotationList = [
            x
            for x in annotationList
            if any(filterstr in x for filterstr in filterString)
        ]

    return annotationList


def addAssumptions(assumptionType, assumption, assumptions):
    assumptions[assumptionType].add(assumption)


speciesNameGrammar = (
    Word(alphanums + "_" + ":#-")
    + Suppress("()")
    + Optional(Suppress("@" + Word(alphanums + "_-")))
) + ZeroOrMore(
    Suppress("+")
    + Word(alphanums + "_" + ":#-")
    + Suppress("()")
    + Optional(Suppress("@" + Word(alphanums + "_-")))
)

nameGrammar = Word(alphanums + "_-") + ":"

rateGrammar = Word("-" + alphanums + "()")

grammar = Suppress(Optional(nameGrammar)) + (
    (Group(speciesNameGrammar) | "0")
    + Suppress(Optional("<") + "->")
    + (Group(speciesNameGrammar) | "0")
    + Suppress(rateGrammar)
) ^ (speciesNameGrammar + Suppress(Optional("<") + "->") + Suppress(rateGrammar))


@memoize
def parseReactions(reaction):
    """
    given a reaction string definition it separates the elements into reactants and products
    >>> parseReactions('A() + B() -> C() k1()')
    [['A', 'B'], ['C']]
    >>> parseReactions('A()@EC + B()@PM -> C()@PM k1()')
    [['A', 'B'], ['C']]
    >>> parseReactions('0 -> A() k1()')
    ['0', ['A']]
    """
    result = grammar.parseString(reaction).asList()
    if len(result) < 2:
        result = [result, []]
    if "<->" in reaction and len(result[0]) == 1 and len(result[1]) == 2:
        result2 = [result[1], result[0]]
        result = result2
    return result


def getAnnotations(annotation):
    """
    parses a libsbml.XMLAttributes annotation object into a list of annotations
    """
    annotationDictionary = []
    if annotation == [] or annotation is None:
        return []
    for index in range(0, annotation.getNumAttributes()):
        annotationDictionary.append(annotation.getValue(index))
    return annotationDictionary
