from utils import readBNGXML
import argparse
import collections
import stateTransitionDiagram as std
import xlwt
import yaml
import arial10
import os
import fnmatch
from collections import defaultdict


def getValidFiles(directory, extension):
    """
    Gets a list of bngl files that could be correctly translated in a given 'directory'
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, "*.{0}".format(extension)):
            matches.append(os.path.join(root, filename))
    return matches


class FitSheetWrapper(object):
    """Try to fit columns to max size of any entry.
    To use, wrap this around a worksheet returned from the
    workbook's add_sheet method, like follows:

        sheet = FitSheetWrapper(book.add_sheet(sheet_name))

    The worksheet interface remains the same: this is a drop-in wrapper
    for auto-sizing columns.
    """

    def __init__(self, sheet):
        self.sheet = sheet
        self.widths = dict()

    def write(self, r, c, label="", *args, **kwargs):
        self.sheet.write(r, c, label, *args, **kwargs)
        width = arial10.fitwidth(label)
        if width > self.widths.get(c, 0):
            self.widths[c] = int(width)
            self.sheet.col(c).width = int(width)

    def __getattr__(self, attr):
        return getattr(self.sheet, attr)


class PrettyDefaultDict(collections.defaultdict):
    __repr__ = dict.__repr__


def getParameterDictionary(bnglNamespace):

    parameterDict = PrettyDefaultDict(lambda: PrettyDefaultDict(set))
    simpleParameterDict = collections.defaultdict(set)

    (
        labels,
        centers,
        contexts,
        products,
        atomicArrays,
        actions,
        doubleAction,
    ) = std.extractCenterContext(bnglNamespace["rules"])

    for label, center, product, rule in zip(
        labels, centers, products, bnglNamespace["rules"]
    ):
        for pattern in product:
            for element in pattern:
                for molecule in element.split("."):
                    for rate in rule[0].rates:
                        value = (
                            bnglNamespace["parameters"][rate]
                            if rate in bnglNamespace["parameters"]
                            else "nma"
                        )
                        moleculeName = molecule.split("(")[0].split("%")[0]
                        component = molecule.split("(")[1].strip(")")
                        parameterDict[moleculeName.lower()][component].add(value)
                        simpleParameterDict[molecule].add(value)

    return parameterDict


def defineConsole():
    """
    defines the program console line commands
    """
    parser = argparse.ArgumentParser(description="SBML to BNGL translator")
    parser.add_argument("-i", "--input", type=str, help="settings file", required=True)
    return parser


def remove_empty_keys(d):
    for k in d.keys():
        if not d[k]:
            del d[k]


def getDifferences(modelNameList, parameterSpace):
    keys = collections.Counter([y.lower() for x in parameterSpace for y in x])

    rowIdx = 0
    parameterDict = {x: defaultdict(set) for x in keys}
    parameterModelDict = {x: defaultdict(list) for x in keys}
    for molecule in keys:
        if keys[molecule] <= 1:
            continue
        rowIdx = -1
        for midx, model in enumerate(parameterSpace):
            # write modelName
            if len(model[molecule]) == 0:
                continue
            rowIdx += 1

            for component in model[molecule]:
                if "!" in component:
                    componentTxt = component.split("!")[0] + ("(association)")
                elif "~0" in component:
                    componentTxt = component.split("~")[0] + ("(repression)")
                elif "~" in component:
                    componentTxt = component.split("~")[0] + ("(activation)")
                else:
                    componentTxt = component + ("(dissociation)")

                if (
                    all(
                        [
                            len(x.intersection(model[molecule][component])) == 0
                            for x in parameterDict[molecule][componentTxt]
                        ]
                    )
                    or len(parameterDict[molecule][componentTxt]) == 0
                ):
                    parameterDict[molecule][componentTxt].add(
                        frozenset(model[molecule][component])
                    )
                    parameterModelDict[molecule][componentTxt].append(
                        modelNameList[midx]
                    )
            removeKeys = []
        for component in parameterDict[molecule]:
            if len(parameterDict[molecule][component]) <= 1:
                removeKeys.append(component)
        for component in removeKeys:
            del parameterDict[molecule][component]
            if component in parameterModelDict[molecule]:
                parameterModelDict[molecule][component]

    remove_empty_keys(parameterDict)
    remove_empty_keys(parameterModelDict)

    import pprint

    print "---"
    pprint.pprint(parameterDict)


def ExcelOutput(modelNameList, parameterSpace):
    keys = collections.Counter([y.lower() for x in parameterSpace for y in x])
    wb = xlwt.Workbook()

    ws = FitSheetWrapper(wb.add_sheet("Units"))
    unitColumn = []
    rowIdx = 0

    for midx, element in enumerate(modelNameList):
        modelName = element.split(".")[:-1]
        modelName = ".".join(modelName)
        ymlName = modelName + ".bngl.yml"

        try:
            with open(ymlName, "r") as f:
                annotationDict = yaml.load(f)
        except IOError:
            continue
        ws.write(midx + 1, 0, modelName)
        for unit in annotationDict["units"]:
            if unit not in unitColumn:
                unitColumn.append(unit)
                ws.write(0, unitColumn.index(unit) + 1, unit)
            # for instance in annotationDict['units'][unit]:
            instance = annotationDict["units"][unit][0]
            if instance["exponent"] == 1:
                ws.write(
                    rowIdx + 1,
                    unitColumn.index(unit) + 1,
                    "{0} ({1})".format(instance["multiplier"], instance["name"]).decode(
                        "utf-8"
                    ),
                )
            else:
                ws.write(
                    rowIdx + 1,
                    unitColumn.index(unit) + 1,
                    "{0}^{2} ({1})".format(
                        instance["multiplier"], instance["name"], instance["exponent"]
                    ).decode("utf-8"),
                )
        rowIdx += 1
    for molecule in keys:
        if keys[molecule] <= 1:
            continue

        sheetName = molecule if len(molecule) <= 31 else molecule[0:31]
        ws = FitSheetWrapper(wb.add_sheet(sheetName))
        componentColumn = []
        rowIdx = -1
        for midx, model in enumerate(parameterSpace):
            # write modelName
            if len(model[molecule]) == 0:
                continue
            rowIdx += 1
            ws.write(rowIdx + 1, 0, modelNameList[midx])
            for component in model[molecule]:
                if component not in componentColumn:
                    componentColumn.append(component)
                    if "!" in component:
                        componentTxt = component.split("!")[0] + ("(association)")
                    elif "~0" in component:
                        componentTxt = component.split("~")[0] + ("(repression)")
                    elif "~" in component:
                        componentTxt = component.split("~")[0] + ("(activation)")
                    else:
                        componentTxt = component + ("(dissociation)")

                    ws.write(0, componentColumn.index(component) + 1, componentTxt)
                data = "/".join(model[molecule][component])
                ws.write(rowIdx + 1, componentColumn.index(component) + 1, data)

    wb.save("19_151_48.xls")


if __name__ == "__main__":
    # parser = defineConsole()
    # namespace = parser.parse_args()
    # inputFile = namespace.input
    # modelNameList = getValidFiles('egfr','xml')
    # modelNameList = getValidFiles('curated','xml')

    modelNameList = getValidFiles("tmp", "xml")
    # modelName = ['egfr/output151.xml']
    parameterSpace = []
    for element in modelNameList:
        parameterSpace.append(getParameterDictionary(readBNGXML.parseFullXML(element)))

    ExcelOutput(modelNameList, parameterSpace)
    getDifferences(modelNameList, parameterSpace)
    """
    with open('19_151_48.csv','wb') as f:
        writer = csv.DictWriter(f, keys)
        writer.writeheader()
        writer.writerows(parameterSpace)
    """
