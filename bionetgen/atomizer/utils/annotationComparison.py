import annotationExtractor as annEx
import argparse
import fnmatch
import argparse
import os
import progressbar
import cPickle as pickle
import numpy as np

# import SBMLparser.utils.characterizeAnnotationLog as cal


def defineConsole():
    parser = argparse.ArgumentParser(description="SBML to BNGL translator")
    parser.add_argument(
        "-m1", "--model1", type=str, help="input SBML model1", required=True
    )
    parser.add_argument(
        "-m2", "--model2", type=str, help="input SBML model2", required=True
    )
    # parser.add_argument('-o','--output-file',type=str,help='output SBML file',required=True)
    return parser


def componentAnalysis(directory):
    componentCount = []
    bindingCount = []
    stateCount = []
    modelComponentDict = {}
    with open(os.path.join(directory, "moleculeTypeDataSet.dump"), "rb") as f:
        moleculeTypesArray = pickle.load(f)
    for model in moleculeTypesArray:
        modelComponentCount = [len(x.components) for x in model[0]]

        bindingComponentCount = [
            len([y for y in x.components if len(y.states) == 0]) for x in model[0]
        ]

        modificationComponentCount = [
            sum([max(1, len(y.states)) for y in x.components]) for x in model[0]
        ]

        modelComponentDict[model[-2]] = {
            "bindingComponents": np.mean(bindingComponentCount),
            "stateComponents": np.mean(modificationComponentCount),
            "componentCount": np.mean(modelComponentCount),
        }
        # bindingCount.append(bindingComponentCount)
        # stateCount.append(modificationComponentCount)
        # componentCount.append(modelComponentCount)

    # interestingCount = [index for index, x in enumerate(componentCount) if np.mean(x) >= atomizeThreshold]
    # componentCount = np.array(componentCount)
    # bindingCount = np.array(bindingCount)
    # stateCount = np.array(stateCount)

    return modelComponentDict
    # plt.show()


def getFiles(directory, extension):
    """
    Gets a list of <*.extension> files. include subdirectories and return the absolute
    path. also sorts by size.
    """
    matches = []
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, "*.{0}".format(extension)):
            matches.append(
                [
                    os.path.join(os.path.abspath(root), filename),
                    os.path.getsize(os.path.join(root, filename)),
                ]
            )

    # sort by size
    # matches.sort(key=lambda filename: filename[1], reverse=False)

    matches = [x[0] for x in matches]

    return matches


def annotationComparison(model1, model2, errorList):
    try:
        annotationExtractor = annEx.AnnotationExtractor(model1)
    except AttributeError:
        # print model1, "doesnt exist"
        return -1
    try:
        modelAnnotations1 = annotationExtractor.getModelAnnotations()
    except AttributeError:
        return -1
    # elementalMolecules = [x for x in annotationExtractor.sct if annotationExtractor.sct[x] == []]
    # complexMolecules1 = [x for x in annotationExtractor.sct if annotationExtractor.sct[x] != []]

    annotationDict1 = annotationExtractor.getAnnotationSystem()

    annotationExtractor = annEx.AnnotationExtractor(model2)
    modelAnnotations2 = annotationExtractor.getModelAnnotations()
    # elementalMolecules = [x for x in annotationExtractor.sct if annotationExtractor.sct[x] == []]
    # complexMolecules2 = [x for x in annotationExtractor.sct if annotationExtractor.sct[x] != [] and x in complexMolecules1]
    annotationDict2 = annotationExtractor.getAnnotationSystem()

    error = 0
    for entry in annotationDict1:
        if entry not in annotationDict2:
            continue
        # for label in ['BQB_HAS_PART','BQB_IS_VERSION_OF','BQB_IS','']
        if not set(
            [x for x in annotationDict2[entry]["BQB_HAS_PART"] if "uniprot" in x]
        ).issubset(
            set([x for x in annotationDict1[entry]["BQB_HAS_PART"] if "uniprot" in x])
        ) and not set(
            [x for x in annotationDict2[entry]["BQB_HAS_PART"] if "uniprot" in x]
        ).issubset(
            set(
                [x for x in annotationDict1[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
            )
        ):
            error += 1

        if not set(
            [x for x in annotationDict2[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
        ).issubset(
            set(
                [x for x in annotationDict1[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
            )
        ) and not set(
            [x for x in annotationDict2[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
        ).issubset(
            set([x for x in annotationDict1[entry]["BQB_HAS_PART"] if "uniprot" in x])
        ):
            error += 1

    if error > 0:
        errorList.extend([model1.split("/")[1]])
        return 0
    return 1


def annotationFileComparison(model1, model2):
    try:
        annotationExtractor = annEx.AnnotationExtractor(model1)
    except AttributeError:
        # print model1, "doesnt exist"
        return -1
    modelAnnotations1 = annotationExtractor.getModelAnnotations()
    # elementalMolecules = [x for x in annotationExtractor.sct if annotationExtractor.sct[x] == []]

    annotationDict1 = annotationExtractor.getAnnotationSystem()

    annotationExtractor = annEx.AnnotationExtractor(model2)
    modelAnnotations2 = annotationExtractor.getModelAnnotations()
    # elementalMolecules = [x for x in annotationExtractor.sct if annotationExtractor.sct[x] == []]
    annotationDict2 = annotationExtractor.getAnnotationSystem()
    error = 0
    totalSet = set()

    for entry in annotationDict1:
        if not set(
            [x for x in annotationDict2[entry]["BQB_HAS_PART"] if "uniprot" in x]
        ).issubset(
            set([x for x in annotationDict1[entry]["BQB_HAS_PART"] if "uniprot" in x])
        ) and not set(
            [x for x in annotationDict2[entry]["BQB_HAS_PART"] if "uniprot" in x]
        ).issubset(
            set(
                [x for x in annotationDict1[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
            )
        ):
            print "--------------+"
            print entry
            difference = set(
                [x for x in annotationDict2[entry]["BQB_HAS_PART"] if "uniprot" in x]
            ).difference(
                set(
                    [
                        x
                        for x in annotationDict1[entry]["BQB_HAS_PART"]
                        if "uniprot" in x
                    ]
                )
            )
            print difference
            print annotationDict1[entry]
            print annotationDict2[entry]
            totalSet = totalSet.union(difference)
            # print set([x for x in annotationDict1[entry]['BQB_HAS_PART'] if 'uniprot' in x])

        if not set(
            [x for x in annotationDict2[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
        ).issubset(
            set(
                [x for x in annotationDict1[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
            )
        ) and not set(
            [x for x in annotationDict2[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
        ).issubset(
            set([x for x in annotationDict1[entry]["BQB_HAS_PART"] if "uniprot" in x])
        ):
            print "--------------"
            print entry
            difference = set(
                [x for x in annotationDict2[entry]["BQB_HAS_VERSION"] if "uniprot" in x]
            ).difference(
                set(
                    [
                        x
                        for x in annotationDict1[entry]["BQB_HAS_VERSION"]
                        if "uniprot" in x
                    ]
                )
            )
            print difference
            totalSet = totalSet.union(difference)

            # print set([x for x in annotationDict1[entry]['BQB_IS_VERSION_OF'] if 'uniprot' in x])
    print totalSet


def batchAnnotationComparison(removedAnnotationsDir, referenceDir):
    referenceFiles = getFiles(referenceDir, "xml")
    progress = progressbar.ProgressBar()
    errorFiles = 0
    counter = 0
    errorList = []
    for fileIdx in progress(range(len(referenceFiles))):
        file = referenceFiles[fileIdx]
        result = annotationComparison(
            os.path.join(removedAnnotationsDir, file.split("/")[-1]), file, errorList
        )
        if result == 0:
            counter += 1
        elif result == -1:
            errorFiles += 1

    print 1 - counter * 1.0 / (
        len(referenceFiles) - errorFiles
    ), counter, errorFiles, len(referenceFiles)
    return errorList


if __name__ == "__main__":

    batch = False

    if batch:
        errorList = batchAnnotationComparison(
            "annotationsExpanded2", "../XMLExamples/curated"
        )

        print errorList
        print len(errorList)
    else:
        annotationFileComparison(
            "annotationsExpanded2/BIOMD0000000022.xml",
            "/home/proto/workspace/RuleWorld/atomizer/XMLExamples/curated/BIOMD0000000022.xml",
        )

    # significanceTreshold = 0.3
    # errorLogDict = {}
    # for fileName in errorList:
    #     errorLogDict[fileName] = cal.processLogFile('../curated/{0}.bngl.log'.format(fileName))
    # modelCharacterization = componentAnalysis('../curated')
    # errorResults = [(x,errorLogDict[x], modelCharacterization['curated/{0}.xml'.format(x)]) for x in errorList if 'curated/{0}.xml'.format(x)
    #        in modelCharacterization if 'forcedModification' not in errorLogDict[x] or errorLogDict[x]['forcedModification'] < significanceTreshold]
    # pprint.pprint(errorResults)
    # print len(errorResults)
    # parser = defineConsole()
    # namespace = parser.parse_args()

    # annotationFileComparison('annotationsExpanded2/BIOMD0000000048.xml', '/home/proto/workspace/RuleWorld/atomizer/XMLExamples/curated/BIOMD0000000048.xml')
