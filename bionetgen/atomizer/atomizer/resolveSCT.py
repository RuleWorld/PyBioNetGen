import marshal
import functools
from . import analyzeSBML
from collections import Counter, defaultdict
import itertools
from copy import deepcopy, copy
from bionetgen.atomizer.utils.util import logMess, memoize, memoizeMapped
from . import atomizationAux as atoAux
import bionetgen.atomizer.utils.pathwaycommons as pwcm


class SCTSolver:
    def __init__(self, database, memoizedResolver=False):
        self.database = database
        self.memoizedResolver = memoizedResolver
        self.graph_map = {}
        self.dg = None

    def createSpeciesCompositionGraph(
        self,
        parser,
        configurationFile,
        namingConventions,
        speciesEquivalences=None,
        bioGridFlag=False,
    ):
        """
        Main method for the SCT creation.

        It first does stoichiometry analysis, then lexical...
        """

        _, rules, _ = parser.getReactions(atomize=True, database=self.database)
        molecules, _, _, _, _, _ = parser.getSpecies()
        self.database.sbmlAnalyzer = analyzeSBML.SBMLAnalyzer(
            parser,
            configurationFile,
            namingConventions,
            speciesEquivalences,
            conservationOfMass=True,
        )

        # classify reactions
        (
            self.database.classifications,
            equivalenceTranslator,
            self.database.eequivalenceTranslator,
            indirectEquivalenceTranslator,
            adhocLabelDictionary,
            lexicalDependencyGraph,
            userEquivalenceTranslator,
        ) = self.database.sbmlAnalyzer.classifyReactions(rules, molecules, {})
        self.database.reactionProperties = (
            self.database.sbmlAnalyzer.getReactionProperties()
        )

        syndecs = [
            1 if i == "Generation" or i == "Decay" else 0
            for i in self.database.classifications
        ]
        # user defined and lexical analysis naming conventions are stored here
        self.database.reactionProperties.update(adhocLabelDictionary)

        (
            self.database.translator,
            self.database.userLabelDictionary,
            self.database.lexicalLabelDictionary,
            self.database.partialUserLabelDictionary,
        ) = self.database.sbmlAnalyzer.getUserDefinedComplexes()
        self.database.dependencyGraph = {}
        self.database.alternativeDependencyGraph = {}
        # fill in the annotation dictionary
        self.database.annotationDict = parser.getFullAnnotation()
        # just molecule names without parenthesis
        strippedMolecules = [x.strip("()") for x in molecules]
        # self.database.annotationDict = {}

        # ###dependency graph
        # binding reactions
        for reaction, classification in zip(rules, self.database.classifications):
            self.bindingReactionsAnalysis(
                self.database.dependencyGraph,
                list(atoAux.parseReactions(reaction)),
                classification,
            )
        # lexical dependency graph contains lexically induced binding compositions. atomizer gives preference to binding obtained this way as opposed to stoichiometry
        # stronger bounds on stoichiometry based binding can be defined in
        # reactionDefinitions.json.

        for element in lexicalDependencyGraph:

            if (
                element in self.database.dependencyGraph
                and element not in self.database.userLabelDictionary
            ):
                if len(lexicalDependencyGraph[element]) == 0:
                    continue
                """
                oldDependency = self.database.dependencyGraph[element]
                
                if sorted(lexicalDependencyGraph[element][0]) in [sorted(x) for x in oldDependency]:
                    # if len(oldDependency) > 1:
                    #    logMess('DEBUG:Atomization', 'Species {0} was confirmed to be {1} based on lexical information'.format(element,lexicalDependencyGraph[element]))
                    self.database.dependencyGraph[
                        element] = lexicalDependencyGraph[element]
                else:
                    # logMess('INFO:Atomization', 'Species {0} was determined to be {1} instead of {2} based on \
                    # lexical information'.format(element,
                    # lexicalDependencyGraph[element], oldDependency))
                """
                if self.database.dependencyGraph[element] != []:
                    self.database.alternativeDependencyGraph[
                        element
                    ] = lexicalDependencyGraph[element]
                else:
                    logMess(
                        "INFO:LAE009",
                        "{0}: being set to be a modification of constructed species {1}".format(
                            element, lexicalDependencyGraph[element][0]
                        ),
                    )
                    atoAux.addToDependencyGraph(
                        self.database.dependencyGraph,
                        element,
                        lexicalDependencyGraph[element][0],
                    )
            else:
                if element not in strippedMolecules:
                    self.database.constructedSpecies.add(element)
                self.database.dependencyGraph[element] = lexicalDependencyGraph[element]
            # Check if I'm using a molecule that hasn't been used yet
            for dependencyCandidate in self.database.dependencyGraph[element]:
                for molecule in [
                    x
                    for x in dependencyCandidate
                    if x not in self.database.dependencyGraph
                ]:
                    # this is a species that was not originally in the model. in case theres conflict later this is
                    # to indicate it is given less priority
                    self.database.dependencyGraph[molecule] = []

        # user defined transformations
        for key in userEquivalenceTranslator:
            for namingEquivalence in userEquivalenceTranslator[key]:
                baseElement = min(namingEquivalence, key=len)
                modElement = max(namingEquivalence, key=len)
                if baseElement not in self.database.dependencyGraph:
                    self.database.dependencyGraph[baseElement] = []
                atoAux.addToDependencyGraph(
                    self.database.dependencyGraph, modElement, [baseElement]
                )

        # self.database.eequivalence translator contains 1:1 equivalences
        # FIXME: do we need this update step or is it enough with the later one?
        # catalysis reactions
        """
        for key in self.database.eequivalenceTranslator:
            for namingEquivalence in self.database.eequivalenceTranslator[key]:
                baseElement = min(namingEquivalence, key=len)
                modElement = max(namingEquivalence, key=len)
                if key != 'Binding':
                    if baseElement not in self.database.dependencyGraph or self.database.dependencyGraph[baseElement] == []:
                        if modElement not in self.database.dependencyGraph or self.database.dependencyGraph[modElement] == []:
                            self.database.dependencyGraph[baseElement] = []
                        # do we have a meaningful reverse dependence?
                        # elif all([baseElement not in x for x in self.database.dependencyGraph[modElement]]):
                        #    atoAux.addToDependencyGraph(self.database.dependencyGraph,baseElement,[modElement])
                        #    continue

                            if baseElement in self.database.annotationDict and modElement in self.database.annotationDict:
                                baseSet = set([y for x in self.database.annotationDict[
                                              baseElement] for y in self.database.annotationDict[baseElement][x]])
                                modSet = set([y for x in self.database.annotationDict[
                                             modElement] for y in self.database.annotationDict[modElement][x]])
                                if len(baseSet.intersection(modSet)) > 0 or len(baseSet) == 0 or len(modSet) == 0:
                                    atoAux.addToDependencyGraph(self.database.dependencyGraph, modElement,
                                                         [baseElement])
                                else:
                                    logMess("ERROR:ANN201", "{0} and {1} have a direct correspondence according to reaction information however their annotations are completely different.".format(
                                        baseElement, modElement))
                            else:
                                atoAux.addToDependencyGraph(self.database.dependencyGraph, modElement,
                                                     [baseElement])
        """
        # include user label information.
        for element in self.database.userLabelDictionary:
            if self.database.userLabelDictionary[element] in [0, [(0,)]]:
                self.database.dependencyGraph[element] = ["0"]
            elif (
                len(self.database.userLabelDictionary[element][0]) == 0
                or element == self.database.userLabelDictionary[element][0][0]
            ):

                self.database.dependencyGraph[element] = []
            else:
                self.database.dependencyGraph[element] = [
                    list(self.database.userLabelDictionary[element][0])
                ]
                # If the user is introducing a new molecule term, add it to the SCT
                if (
                    self.database.userLabelDictionary[element][0][0]
                    not in self.database.dependencyGraph
                ):
                    self.database.dependencyGraph[
                        self.database.userLabelDictionary[element][0][0]
                    ] = []

        # add species elements defined by the user into the naming convention
        # definition
        molecules.extend(
            [
                "{0}()".format(x)
                for x in self.database.userLabelDictionary
                if "{0}()".format(x) not in molecules
            ]
        )
        # recalculate 1:1 equivalences now with binding information
        (
            _,
            _,
            self.database.eequivalenceTranslator2,
            _,
            adhocLabelDictionary,
            _,
            _,
        ) = self.database.sbmlAnalyzer.classifyReactions(
            rules, molecules, self.database.dependencyGraph
        )
        self.database.reactionProperties.update(adhocLabelDictionary)
        # update catalysis equivalences
        # catalysis reactions
        for key in self.database.eequivalenceTranslator2:
            for namingEquivalence in self.database.eequivalenceTranslator2[key]:

                baseElement = min(namingEquivalence, key=len)
                modElement = max(namingEquivalence, key=len)
                # dont overwrite user information
                if (
                    key != "Binding"
                    and modElement not in self.database.userLabelDictionary
                ):
                    if baseElement not in self.database.dependencyGraph:
                        self.database.constructedSpecies.add(baseElement)
                        self.database.dependencyGraph[baseElement] = []
                    if modElement not in self.database.dependencyGraph or not [
                        True
                        for x in self.database.dependencyGraph[modElement]
                        if baseElement in x and len(x) > 1
                    ]:
                        if (
                            baseElement in self.database.annotationDict
                            and modElement in self.database.annotationDict
                        ):
                            baseSet = set(
                                [
                                    y
                                    for x in self.database.annotationDict[baseElement]
                                    for y in self.database.annotationDict[baseElement][
                                        x
                                    ]
                                ]
                            )
                            modSet = set(
                                [
                                    y
                                    for x in self.database.annotationDict[modElement]
                                    for y in self.database.annotationDict[modElement][x]
                                ]
                            )
                            if (
                                len(baseSet.intersection(modSet)) > 0
                                or len(baseSet) == 0
                                or len(modSet) == 0
                            ):
                                if modElement not in self.database.dependencyGraph:
                                    # if the entry doesnt exist from previous information accept this
                                    atoAux.addToDependencyGraph(
                                        self.database.dependencyGraph,
                                        modElement,
                                        [baseElement],
                                    )
                                else:
                                    # otherwise add it to the lexical repository
                                    atoAux.addToDependencyGraph(
                                        self.database.alternativeDependencyGraph,
                                        modElement,
                                        [baseElement],
                                    )
                            else:
                                baseDB = set(
                                    [
                                        x.split("/")[-2]
                                        for x in baseSet
                                        if "identifiers.org" in x
                                    ]
                                )
                                modDB = set(
                                    [
                                        x.split("/")[-2]
                                        for x in modSet
                                        if "identifiers.org" in x
                                    ]
                                )
                                # it is still ok if they each refer to different self.databases
                                if len(baseDB.intersection(modDB)) == 0:
                                    if modElement not in self.database.dependencyGraph:
                                        # if the entry doesnt exist from previous information accept this
                                        atoAux.addToDependencyGraph(
                                            self.database.dependencyGraph,
                                            modElement,
                                            [baseElement],
                                        )
                                    else:
                                        # otherwise add it to the lexical repository
                                        atoAux.addToDependencyGraph(
                                            self.database.alternativeDependencyGraph,
                                            modElement,
                                            [baseElement],
                                        )
                                else:
                                    logMess(
                                        "WARNING:ANN201",
                                        "{0} and {1} have a direct correspondence according to reaction information however their annotations are completely different.".format(
                                            baseElement, modElement
                                        ),
                                    )
                        else:
                            atoAux.addToDependencyGraph(
                                self.database.dependencyGraph, modElement, [baseElement]
                            )
                    else:
                        logMess(
                            "WARNING:ATO114",
                            "Definition conflict between binding information {0} and lexical analyis {1} for molecule {2},\
    choosing binding".format(
                                self.database.dependencyGraph[modElement],
                                baseElement,
                                modElement,
                            ),
                        )

        # non lexical-analysis catalysis reactions
        if self.database.forceModificationFlag:
            for reaction, classification in zip(rules, self.database.classifications):
                preaction = list(atoAux.parseReactions(reaction))
                if len(preaction[0]) == 1 and len(preaction[1]) == 1:
                    if (preaction[0][0] in [0, "0"]) or (preaction[1][0] in [0, "0"]):
                        continue
                    if preaction[1][0].lower() in preaction[0][0].lower() or len(
                        preaction[1][0]
                    ) < len(preaction[0][0]):
                        base = preaction[1][0]
                        mod = preaction[0][0]
                    else:
                        mod = preaction[1][0]
                        base = preaction[0][0]
                    if (
                        self.database.dependencyGraph[mod] == []
                        and mod not in self.database.userLabelDictionary
                    ):

                        if (
                            base in self.database.userLabelDictionary
                            and self.database.userLabelDictionary[base] == 0
                        ):
                            continue
                        if (
                            mod in self.database.userLabelDictionary
                            and self.database.userLabelDictionary[mod] == 0
                        ):
                            continue
                        if [mod] in self.database.dependencyGraph[base]:
                            continue

                        # can we just match it up through existing species instead of forcing a modification?
                        greedyMatch = (
                            self.database.sbmlAnalyzer.greedyModificationMatching(
                                mod, self.database.dependencyGraph.keys()
                            )
                        )

                        if greedyMatch not in [-1, -2, []]:
                            self.database.dependencyGraph[mod] = [greedyMatch]
                            if mod in self.database.alternativeDependencyGraph:
                                del self.database.alternativeDependencyGraph[mod]
                            logMess(
                                "INFO:LAE006",
                                "{0}: Mapped to {1} using lexical analysis/greedy matching".format(
                                    mod, greedyMatch
                                ),
                            )
                            continue

                        # if the annotations have no overlap whatsoever don't force
                        # this modifications
                        if (
                            base in self.database.annotationDict
                            and mod in self.database.annotationDict
                        ):
                            baseSet = set(
                                [
                                    y
                                    for x in self.database.annotationDict[base]
                                    for y in self.database.annotationDict[base][x]
                                ]
                            )
                            modSet = set(
                                [
                                    y
                                    for x in self.database.annotationDict[mod]
                                    for y in self.database.annotationDict[mod][x]
                                ]
                            )
                            if (
                                (len(baseSet.intersection(modSet))) == 0
                                and len(baseSet) > 0
                                and len(modSet) > 0
                            ):
                                baseDB = set(
                                    [
                                        x.split("/")[-2]
                                        for x in baseSet
                                        if "identifiers.org" in x
                                    ]
                                )
                                modDB = set(
                                    [
                                        x.split("/")[-2]
                                        for x in modSet
                                        if "identifiers.org" in x
                                    ]
                                )
                                # we stil ahve to check that they both reference the same self.database
                                if len(baseDB.intersection(modDB)) > 0:
                                    logMess(
                                        "WARNING:ANN201",
                                        "{0} and {1} have a direct correspondence according to reaction information however their annotations are completely different.".format(
                                            base, mod
                                        ),
                                    )
                                    continue
                        self.database.dependencyGraph[mod] = [[base]]

        """
        #complex catalysis reactions
        for key in indirectEquivalenceTranslator:
            #first remove these entries from the dependencyGraph since
            #they are not true bindingReactions
            for namingEquivalence in indirectEquivalenceTranslator[key]:
                removedElement = ''
                tmp3 = deepcopy(namingEquivalence[1])
                if tmp3 in self.database.dependencyGraph[namingEquivalence[0][0]]:
                    removedElement = namingEquivalence[0][0]
                elif tmp3 in self.database.dependencyGraph[namingEquivalence[0][1]]:
                    removedElement = namingEquivalence[0][1]

                else:
                    tmp3.reverse()
                    if tmp3 in self.database.dependencyGraph[namingEquivalence[0][0]]:
                        removedElement = namingEquivalence[0][0]

                    elif tmp3 in self.database.dependencyGraph[namingEquivalence[0][1]]:
                        removedElement = namingEquivalence[0][1]


                #then add the new, true dependencies
                #if its not supposed to be a basic element
                tmp = [x for x in namingEquivalence[1] if x not in namingEquivalence[2]]
                tmp.extend([x for x in namingEquivalence[2] if x not in namingEquivalence[1]])
                tmp2 = deepcopy(tmp)
                tmp2.reverse()
                ##TODO: map back for the elements in namingEquivalence[2]
                if tmp not in self.database.dependencyGraph[namingEquivalence[3][0]] \
                    and tmp2 not in self.database.dependencyGraph[namingEquivalence[3][0]]:
                    if sorted(tmp) == sorted(tmp3):
                        continue
                    if all(x in self.database.dependencyGraph for x in tmp):
                        if removedElement in self.database.dependencyGraph:
                            self.database.dependencyGraph[removedElement].remove(tmp3)
                        logMess('INFO:Atomization','Removing {0}={1} and adding {2}={3} instead\
     from the dependency list since we determined it is not a true binding reaction based on lexical analysis'\
                        .format(removedElement,tmp3,namingEquivalence[3][0],tmp))
                        self.database.dependencyGraph[namingEquivalence[3][0]] = [tmp]
                    else:
                        logMess('WARNING:Atomization','We determined that {0}={1} based on lexical analysis instead of \
    {2}={3} (stoichiometry) but one of the constituent components in {1} is not a molecule so no action was taken'.format(namingEquivalence[3][0],
    tmp,removedElement,tmp3))
        #user defined stuff
    """

        # stuff obtained from string similarity analysis
        for element in self.database.lexicalLabelDictionary:
            # similarity analysis has less priority than anything we discovered
            # before
            if (
                element in self.database.dependencyGraph
                and len(self.database.dependencyGraph[element]) > 0
            ):
                continue

            if (
                len(self.database.lexicalLabelDictionary[element][0]) == 0
                or element == self.database.lexicalLabelDictionary[element][0][0]
            ):
                self.database.constructedSpecies.add(element)
                atoAux.addToDependencyGraph(self.database.dependencyGraph, element, [])
            else:
                # logMess('INFO:Atomization', ' added induced speciesStructure {0}={1}'
                #         .format(element, self.database.lexicalLabelDictionary[element][0]))
                self.database.dependencyGraph[element] = [
                    list(self.database.lexicalLabelDictionary[element][0])
                ]

        # Now let's go for annotation analysis and last resort stuff on the remaining orphaned molecules
        orphanedSpecies = [
            x
            for x in strippedMolecules
            if x not in self.database.dependencyGraph
            or self.database.dependencyGraph[x] == []
        ]
        orphanedSpecies.extend(
            [
                x
                for x in self.database.dependencyGraph
                if self.database.dependencyGraph[x] == [] and x not in orphanedSpecies
            ]
        )

        # Fill SCT with annotations for those species that still dont have any
        # mapping

        annotationDependencyGraph, _ = self.fillSCTwithAnnotationInformation(
            orphanedSpecies, self.database.annotationDict
        )

        # use an empty dictionary if we wish to turn off annotation information in atomization
        # annotationDependencyGraph = {}

        for annotatedSpecies in annotationDependencyGraph:
            if (
                len(annotationDependencyGraph[annotatedSpecies]) > 0
                and annotatedSpecies not in self.database.userLabelDictionary
            ):
                atoAux.addToDependencyGraph(
                    self.database.dependencyGraph,
                    annotatedSpecies,
                    annotationDependencyGraph[annotatedSpecies][0],
                )
                logMess(
                    "INFO:ANN004",
                    "Added equivalence from annotation information {0}={1}".format(
                        annotatedSpecies, annotationDependencyGraph[annotatedSpecies][0]
                    ),
                )
                for element in annotationDependencyGraph[annotatedSpecies][0]:
                    # in case one of the compositional elements is not yet in the
                    # dependency graph
                    if element not in self.database.dependencyGraph:
                        atoAux.addToDependencyGraph(
                            self.database.dependencyGraph, element, []
                        )

        # can we now add information to the non orphaned species? maybe annotation tells me stuff that contradicts the reaction-network
        nonOrphanedSpecies = [x for x in strippedMolecules if x not in orphanedSpecies]

        annotationDependencyGraph, _ = self.fillSCTwithAnnotationInformation(
            nonOrphanedSpecies,
            self.database.annotationDict,
            self.database,
            tentativeFlag=True,
        )

        orphanedSpecies = [
            x
            for x in strippedMolecules
            if x not in self.database.dependencyGraph
            or self.database.dependencyGraph[x] == []
        ]
        orphanedSpecies.extend(
            [
                x
                for x in self.database.dependencyGraph
                if self.database.dependencyGraph[x] == [] and x not in orphanedSpecies
            ]
        )

        orphanedSpecies.extend(self.database.constructedSpecies)
        strippedMolecules.extend(
            [x.strip("()") for x in self.database.constructedSpecies]
        )
        # TODO: merge both lists and use them as a tiebreaker for consolidation
        # completeAnnotationDependencyGraph, completePartialMatches = fillSCTwithAnnotationInformation(strippedMolecules, annotationDict, self.database, False)
        # pure lexical analysis for the remaining orphaned molecules
        (
            tmpDependency,
            self.database.tmpEquivalence,
        ) = self.database.sbmlAnalyzer.findClosestModification(
            orphanedSpecies,
            strippedMolecules,
            self.database.annotationDict,
            self.database.dependencyGraph,
        )

        for species in tmpDependency:
            if species not in self.database.userLabelDictionary:
                if tmpDependency[species] == []:
                    atoAux.addToDependencyGraph(
                        self.database.dependencyGraph, species, []
                    )
                for instance in tmpDependency[species]:
                    atoAux.addToDependencyGraph(
                        self.database.dependencyGraph, species, instance
                    )
                    if (
                        len(instance) == 1
                        and instance[0] not in self.database.dependencyGraph
                    ):
                        atoAux.addToDependencyGraph(
                            self.database.dependencyGraph, instance[0], []
                        )

        orphanedSpecies = [
            x
            for x in strippedMolecules
            if x not in self.database.dependencyGraph
            or self.database.dependencyGraph[x] == []
        ]

        orphanedSpecies.extend(
            [
                x
                for x in self.database.dependencyGraph
                if self.database.dependencyGraph[x] == [] and x not in orphanedSpecies
            ]
        )

        orphanedSpecies.extend(self.database.constructedSpecies)
        # greedy lexical analysis for the remaining orhpaned species
        for reactant in orphanedSpecies:
            greedyMatch = self.database.sbmlAnalyzer.greedyModificationMatching(
                reactant, self.database.dependencyGraph.keys()
            )
            if greedyMatch not in [-1, -2, []]:
                atoAux.addToDependencyGraph(
                    self.database.dependencyGraph, reactant, greedyMatch
                )
                logMess(
                    "INFO:LAE006",
                    "Mapped {0} to {1} using lexical analysis/greedy matching".format(
                        reactant, greedyMatch
                    ),
                )
        if len(self.database.constructedSpecies) > 0:
            logMess(
                "INFO:SCT031",
                "The following species names do not appear in the original model but where created to have more appropiate naming conventions: [{0}]".format(
                    ",".join(self.database.constructedSpecies)
                ),
            )

        # initialize and remove zero elements
        (
            self.database.prunnedDependencyGraph,
            self.database.weights,
            unevenElementDict,
            self.database.artificialEquivalenceTranslator,
        ) = self.consolidateDependencyGraph(
            self.database.dependencyGraph,
            equivalenceTranslator,
            self.database.eequivalenceTranslator,
            self.database.sbmlAnalyzer,
        )
        return self.database

    def bindingReactionsAnalysis(self, dependencyGraph, reaction, classification):
        """
        adds addBond based reactions based dependencies to the dependency graph

        >>> dg = dg2 = {}
        >>> dummy = SCTSolver(None)
        >>> dummy.bindingReactionsAnalysis(dg, [['A', 'B'], ['C']], 'Binding')
        >>> dg == {'A': [], 'C': [['A', 'B']], 'B': []}
        True
        >>> dummy.bindingReactionsAnalysis(dg2, [['C'], ['A', 'B']], 'Binding')
        >>> dg2 == {'A': [], 'C': [['A', 'B']], 'B': []}
        True
        """
        totalElements = [item for sublist in reaction for item in sublist]
        for element in totalElements:
            atoAux.addToDependencyGraph(dependencyGraph, element, [])
            if classification == "Binding":
                if len(reaction[1]) == 1 and element not in reaction[0]:
                    atoAux.addToDependencyGraph(dependencyGraph, element, reaction[0])
                elif len(reaction[0]) == 1 and element not in reaction[1]:
                    atoAux.addToDependencyGraph(dependencyGraph, element, reaction[1])

    def fillSCTwithAnnotationInformation(
        self, orphanedSpecies, annotationDict, logResults=True, tentativeFlag=False
    ):
        # annotation handling
        exactMatches = defaultdict(list)
        partialMatches = defaultdict(list)
        strongIntersectionMatches = defaultdict(list)
        intersectionMatches = defaultdict(list)
        # iterate over all pairs of orphaned species
        for combinationParticle in itertools.combinations(orphanedSpecies, 2):
            # compare annotations
            if (
                combinationParticle[0] in annotationDict
                and combinationParticle[1] in annotationDict
            ):

                sortedPair = sorted(list(combinationParticle), key=len)
                # get unary keys
                unaryAnnotation1 = [
                    y
                    for x in annotationDict[combinationParticle[0]]
                    for y in annotationDict[combinationParticle[0]][x]
                    if x
                    in [
                        "BQM_IS_DESCRIBED_BY",
                        "BQB_IS_VERSION_OF",
                        "BQB_IS",
                        "BQB_ENCODES",
                    ]
                    and ("uniprot" in y or "chebi" in y)
                ]
                unaryAnnotation2 = [
                    y
                    for x in annotationDict[combinationParticle[1]]
                    for y in annotationDict[combinationParticle[1]][x]
                    if x
                    in [
                        "BQM_IS_DESCRIBED_BY",
                        "BQB_IS_VERSION_OF",
                        "BQB_IS",
                        "BQB_ENCODES",
                    ]
                    and ("uniprot" in y or "chebi" in y)
                ]

                # get compositional keys
                compositionalAnnotation1 = [
                    y
                    for x in annotationDict[combinationParticle[0]]
                    for y in annotationDict[combinationParticle[0]][x]
                    if x in ["BQB_HAS_PART", "BQB_HAS_VERSION"]
                    and ("uniprot" in y or "chebi" in y)
                ]
                compositionalAnnotation2 = [
                    y
                    for x in annotationDict[combinationParticle[1]]
                    for y in annotationDict[combinationParticle[1]][x]
                    if x in ["BQB_HAS_PART", "BQB_HAS_VERSION"]
                    and ("uniprot" in y or "chebi" in y)
                ]
                # unary keys match
                if any([x in unaryAnnotation2 for x in unaryAnnotation1]):

                    exactMatches[sortedPair[1]].append([sortedPair[0]])
                # one composes the other
                elif any([x in compositionalAnnotation1 for x in unaryAnnotation2]):
                    # if combinationParticle[0] not in partialMatches:
                    #    partialMatches[combinationParticle[0]].append([])
                    partialMatches[combinationParticle[0]].append(
                        [combinationParticle[1]]
                    )

                elif any([x in compositionalAnnotation2 for x in unaryAnnotation1]):
                    # if combinationParticle[1] not in partialMatches:
                    #    partialMatches[combinationParticle[1]].append([])
                    partialMatches[combinationParticle[1]].append(
                        [combinationParticle[0]]
                    )
                elif (
                    set(compositionalAnnotation1) == set(compositionalAnnotation2)
                    and len(
                        [
                            x in compositionalAnnotation2
                            for x in compositionalAnnotation1
                        ]
                    )
                    > 0
                ):
                    strongIntersectionMatches[sortedPair[1]].append([sortedPair[0]])
                # they intersect
                elif any(
                    [x in compositionalAnnotation2 for x in compositionalAnnotation1]
                ):

                    intersectionMatches[sortedPair[1]].append([sortedPair[0]])
                    # intersectionMatches[combinationParticle[0]].append(combinationParticle[1])
        # create unary groups

        exactMatches = self.consolidateDependencyGraph(
            dict(exactMatches), {}, {}, self.database.sbmlAnalyzer, loginformation=False
        )[0]

        if logResults:
            for x in [y for y in exactMatches if len(exactMatches[y]) > 0]:
                if not tentativeFlag:
                    logMess(
                        "INFO:ANN001",
                        "{0}:{1}: there is a direct equivalence between these sets according to annotation information. No action was taken".format(
                            x, exactMatches[x][0][0]
                        ),
                    )
                else:
                    if not (
                        x in self.database.dependencyGraph
                        and exactMatches[x][0][0] in self.database.dependencyGraph
                        and self.database.dependencyGraph[x]
                        == self.database.dependencyGraph[exactMatches[x][0][0]]
                    ):
                        logMess(
                            "WARNING:ANN101",
                            "{0}:{1} were determined to be equivalent according to annotation information. Please confirm from user information".format(
                                x, exactMatches[x][0][0]
                            ),
                        )

        # create strong intersection groups

        strongIntersectionMatches = {
            x: strongIntersectionMatches[x]
            for x in strongIntersectionMatches
            if x not in partialMatches
        }
        strongIntersectionMatches.update(exactMatches)
        strongIntersectionMatches = self.consolidateDependencyGraph(
            dict(strongIntersectionMatches),
            {},
            {},
            self.database.sbmlAnalyzer,
            loginformation=False,
        )[0]
        if logResults:
            for x in [
                y
                for y in strongIntersectionMatches
                if len(strongIntersectionMatches[y]) > 0
            ]:
                if x not in exactMatches:
                    if not tentativeFlag:
                        logMess(
                            "INFO:ANN002",
                            "{0}: can exactly match {1} according to annotation information. No action was taken".format(
                                x, strongIntersectionMatches[x]
                            ),
                        )
                    else:
                        if not (
                            x in self.database.dependencyGraph
                            and strongIntersectionMatches[x][0][0]
                            in self.database.dependencyGraph
                            and self.database.dependencyGraph[x]
                            == self.database.dependencyGraph[
                                strongIntersectionMatches[x][0][0]
                            ]
                        ):
                            logMess(
                                "WARNING:ANN101",
                                "{0}: was determined to exactly match {1} according to annotation information. Please confirm from user information".format(
                                    x, strongIntersectionMatches[x]
                                ),
                            )
        # create partial intersection groups
        """
        intersectionMatches = {x: intersectionMatches[x] for x in intersectionMatches if x not in partialMatches and x not in strongIntersectionMatches}
        intersectionMatches.update(exactMatches)


        intersectionMatches = consolidateDependencyGraph(dict(intersectionMatches), {}, {}, self.database.sbmlAnalyzer, self.database, loginformation=False)[0]
        if logResults:
            for x in intersectionMatches:
                if x not in exactMatches:
                    logMess('INFO:ANN002', '{0}: was determined to be partially match {1} according to annotation information.'.format(
                        x, intersectionMatches[x]))

        partialMatches = consolidateDependencyGraph(
            dict(partialMatches), {}, {}, self.database.sbmlAnalyzer, self.database, loginformation=False)[0]

        if logResults:
            for x in partialMatches:
                if partialMatches[x] != []:
                    logMess('INFO:ANN003', '{0}: is thought to be partially composed of reactants {1} according to annotation information. Please verify stoichiometry'.format(
                        x, partialMatches[x]))

        # validAnnotationPairs.sort()

        intersectionMatches.update(strongIntersectionMatches)
        """
        return intersectionMatches, partialMatches

    def consolidateDependencyGraph(
        self,
        dependencyGraph,
        equivalenceTranslator,
        equivalenceDictionary,
        sbmlAnalyzer,
        loginformation=True,
    ):
        """
        The second part of the Atomizer algorithm, once the lexical and stoichiometry information has been extracted
        it is time to state all elements of the system in unequivocal terms of their molecule types
        """

        equivalenceTranslator = {}

        def selectBestCandidate(
            reactant,
            candidates,
            dependencyGraph,
            sbmlAnalyzer,
            equivalenceTranslator=equivalenceTranslator,
            equivalenceDictionary=equivalenceDictionary,
        ):

            tmpCandidates = []
            modifiedElementsPerCandidate = []
            unevenElements = []
            candidateDict = {}
            for individualAnswer in candidates:
                try:
                    tmpAnswer = []
                    flag = True
                    if len(individualAnswer) == 1 and individualAnswer[0] == reactant:
                        continue
                    modifiedElements = []
                    for chemical in individualAnswer:

                        # we cannot handle tuple naming conventions for now
                        if type(chemical) == tuple:
                            flag = False
                            continue
                        # associate elements in the candidate description with their
                        # modified version
                        rootChemical = self.resolveDependencyGraph(
                            dependencyGraph, chemical
                        )
                        mod = self.resolveDependencyGraph(
                            dependencyGraph, chemical, True
                        )
                        if mod != []:
                            modifiedElements.extend(mod)
                        for element in rootChemical:
                            if len(element) == 1 and type(element[0]) == tuple:
                                continue
                            if element == chemical:
                                tmpAnswer.append(chemical)
                            elif type(element) == tuple:
                                tmpAnswer.append(element)
                            else:
                                tmpAnswer.append(element[0])
                    modifiedElementsPerCandidate.append(modifiedElements)
                    if flag:
                        tmpAnswer = sorted(tmpAnswer)
                        tmpCandidates.append(tmpAnswer)
                except atoAux.CycleError:
                    if loginformation:
                        logMess(
                            "ERROR:SCT221",
                            "{0}:{1}:Dependency cycle found when mapping molecule to candidate".format(
                                reactant, individualAnswer[0]
                            ),
                        )
                    continue
            # we cannot handle tuple naming conventions for now
            if len(tmpCandidates) == 0:
                # logMess('CRITICAL:Atomization', 'I dont know how to process these candidates and I have no \
                # way to make an educated guess. Politely refusing to translate
                # {0}={1}.'.format(reactant, candidates))
                return None, None, None
            originalTmpCandidates = deepcopy(tmpCandidates)
            # if we have more than one modified element for a single reactant
            # we can try to  choose the one that is most similar to the original
            # reactant
            # FIXME:Fails if there is a double modification
            newModifiedElements = {}
            # modifiedElementsCounter = Counter()
            modifiedElementsCounters = [Counter() for x in range(len(candidates))]
            # keep track of how many times we need to modify elements in the candidate description
            # FIXME: This only keeps track of the stuff in the fist candidates list
            for idx, modifiedElementsInCandidate in enumerate(
                modifiedElementsPerCandidate
            ):
                for element in modifiedElementsInCandidate:
                    if element[0] not in newModifiedElements or element[1] == reactant:
                        newModifiedElements[element[0]] = element[1]
                    modifiedElementsCounters[idx][element[0]] += 1

            # actually modify elements and store final version in tmpCandidates
            # if tmpCandidates[1:] == tmpCandidates[:-1] or len(tmpCandidates) ==
            # 1:

            for tmpCandidate, modifiedElementsCounter in zip(
                tmpCandidates, modifiedElementsCounters
            ):
                flag = True
                while flag:
                    flag = False
                    for idx, chemical in enumerate(tmpCandidate):
                        if modifiedElementsCounter[chemical] > 0:
                            modifiedElementsCounter[chemical] -= 1
                            tmpCandidate[idx] = newModifiedElements[chemical]
                            flag = True
                            break
            candidateDict = {tuple(x): y for x, y in zip(tmpCandidates, candidates)}
            bcan = []
            btmp = []
            borig = []
            # filter out those dependencies to the 0 element

            # if this is related to the zero element
            if len(tmpCandidates) == 1 and tmpCandidates[0] == ["0"]:
                return ["0"], None, None

            for candidate, tmpcandidate, originaltmpcandidate in zip(
                candidates, tmpCandidates, originalTmpCandidates
            ):
                if originaltmpcandidate != ["0"]:
                    bcan.append(candidate)
                    btmp.append(tmpcandidate)
                    borig.append(originaltmpcandidate)
            candidates = bcan
            tmpCandidates = btmp
            originalTmpCandidates = borig

            if len(tmpCandidates) == 0:
                return None, None, None

            # FIXME: I have no idea wtf this is doing so im commenting it out. i
            # think it's old code that is no longer ncessary
            """
            # update candidate chemical references to their modified version if required
            if len(tmpCandidates) > 1:
                # temporal solution for defaulting to the first alternative
                totalElements = [y for x in tmpCandidates for y in x]
                elementDict = {}
                for word in totalElements:
                    if word not in elementDict:
                        elementDict[word] = 0
                    elementDict[word] += 1
                newTmpCandidates = [[]]
                for element in elementDict:
                    if elementDict[element] % len(tmpCandidates) == 0:
                        newTmpCandidates[0].append(element)
                    #elif elementDict[element] % len(tmpCandidates) != 0 and re.search('(_|^){0}(_|$)'.format(element),reactant):
                    #    newTmpCandidates[0].append(element)
                    #    unevenElements.append([element])
                    else:
                        logMess('WARNING:Atomization', 'Are these actually the same? {0}={1}.'.format(reactant,candidates))
                        unevenElements.append(element)
                flag = True
                # FIXME:this should be done on newtmpCandidates instead of tmpcandidates
                while flag:
                    flag = False
                    for idx, chemical in enumerate(tmpCandidates[0]):
                        if chemical in newModifiedElements: #and newModifiedElements[chemical] in reactant:
                            tmpCandidates[0][idx] = newModifiedElements[chemical]
                            flag = True
                            break
            """
            # if all the candidates are about modification changes to a complex
            # then try to do it through lexical analysis
            if (
                all([len(candidate) == 1 for candidate in candidates])
                and candidates[0][0] != reactant
                and len(tmpCandidates[0]) > 1
            ):
                if reactant is not None:
                    pass

                # analyze based on standard modifications
                # lexCandidate, translationKeys, tmpequivalenceTranslator = sbmlAnalyzer.analyzeSpeciesModification(candidates[0][0], reactant, originalTmpCandidates[0])
                # print '++++'
                (
                    lexCandidate,
                    translationKeys,
                    tmpequivalenceTranslator,
                ) = sbmlAnalyzer.analyzeSpeciesModification2(
                    candidates[0][0], reactant, originalTmpCandidates[0]
                )
                # lexCandidate, translationKeys, tmpequivalenceTranslator = sbmlAnalyzer.analyzeSpeciesModification(candidates[0][0], reactant, tmpCandidates[0])            # FIXME: this is iffy. is it always an append modification? could be prepend
                # lexCandidate = None
                if lexCandidate is not None:
                    lexCandidate = tmpCandidates[0][
                        originalTmpCandidates[0].index(lexCandidate)
                    ]
                    if translationKeys[0] + lexCandidate in dependencyGraph:
                        lexCandidateModification = translationKeys[0] + lexCandidate
                    else:
                        lexCandidateModification = lexCandidate + translationKeys[0]

                    for element in tmpequivalenceTranslator:
                        if element not in equivalenceTranslator:
                            equivalenceTranslator[element] = []
                        equivalenceTranslator[element].append(
                            (lexCandidate, lexCandidateModification)
                        )
                    while lexCandidate in tmpCandidates[0]:
                        tmpCandidates[0].remove(lexCandidate)
                        tmpCandidates[0].append(lexCandidateModification)
                        break
                    if lexCandidateModification not in dependencyGraph:
                        logMess(
                            "WARNING:SCT711",
                            "While analyzing {0}={1} we discovered equivalence {2}={3}, please verify \
    this the correct behavior or provide an alternative for {0}".format(
                                reactant,
                                tmpCandidates[0],
                                lexCandidateModification,
                                lexCandidate,
                            ),
                        )
                    dependencyGraph[lexCandidateModification] = [[lexCandidate]]

                    return [tmpCandidates[0]], unevenElements, candidates

                else:
                    fuzzyCandidateMatch = None
                    """
                    if nothing else works and we know the result is a bimolecular
                    complex and we know which are the basic reactants then try to
                    do fuzzy string matching between the two.
                    TODO: extend this to more than 2 molecule complexes.
                    """
                    if len(tmpCandidates[0]) == 2:
                        tmpmolecules = []
                        tmpmolecules.extend(originalTmpCandidates[0])
                        tmpmolecules.extend(tmpCandidates[0])
                        # FIXME: Fuzzy artificial reaction is using old methods. Try to fix this
                        # or maybe not, no one was using it and when it was used it was wrong
                        # fuzzyCandidateMatch = sbmlAnalyzer.fuzzyArtificialReaction(originalTmpCandidates[0],[reactant],tmpmolecules)
                        fuzzyCandidateMatch = None
                    if fuzzyCandidateMatch is not None:
                        # logMess('INFO:Atomization', 'Used fuzzy string matching from {0} to {1}'.format(reactant, fuzzyCandidateMatch))
                        return [fuzzyCandidateMatch], unevenElements, candidates
                    else:
                        # map based on greedy matching
                        greedyMatch = sbmlAnalyzer.greedyModificationMatching(
                            reactant, dependencyGraph.keys()
                        )
                        if greedyMatch not in [-1, -2]:
                            return (
                                selectBestCandidate(
                                    reactant,
                                    [greedyMatch],
                                    dependencyGraph,
                                    sbmlAnalyzer,
                                )[0],
                                unevenElements,
                                candidates,
                            )

                        # last ditch attempt using straighforward lexical analysis
                        (
                            tmpDependency,
                            tmpEquivalence,
                        ) = sbmlAnalyzer.findClosestModification(
                            [reactant],
                            dependencyGraph.keys(),
                            self.database.annotationDict,
                            self.database.dependencyGraph,
                        )
                        if (
                            reactant in tmpDependency
                            and tmpDependency[reactant] in tmpCandidates[0]
                        ):
                            for element in tmpDependency:
                                if element not in dependencyGraph:
                                    dependencyGraph[element] = tmpDependency[element]
                            for element in tmpEquivalence:
                                if element not in equivalenceDictionary:
                                    equivalenceDictionary[element] = []
                                for equivalence in tmpEquivalence[element]:
                                    if (
                                        equivalence[0]
                                        not in equivalenceDictionary[element]
                                    ):
                                        equivalenceDictionary[element].append(
                                            equivalence[0]
                                        )
                            if len(tmpDependency.keys()) > 0:
                                return (
                                    tmpDependency[reactant],
                                    unevenElements,
                                    candidates,
                                )
                        # XXX: be careful of this change. This basically forces changes to happen
                        # the ive no idea whats going on branch
                        # modificationCandidates = {}
                        # if modificationCandidates == {}:

                        activeCandidates = []
                        for individualCandidate in tmpCandidates:
                            for tmpCandidate in individualCandidate:
                                activeQuery = None
                                uniprotkey = atoAux.getURIFromSBML(
                                    tmpCandidate, self.database.parser, ["uniprot"]
                                )
                                if len(uniprotkey) > 0:
                                    uniprotkey = uniprotkey[0].split("/")[-1]
                                    activeQuery = pwcm.queryActiveSite(uniprotkey, None)
                                if activeQuery and len(activeQuery) > 0:
                                    activeCandidates.append(tmpCandidate)
                                    # enter modification information to self.database
                                    # logMess('INFO:SCT051', '{0}:Determined that {0} has an active site for modication'.format(reactant, tmpCandidate))
                                    # return [individualCandidate], unevenElements, candidates
                                # we want relevant biological names, its useless if they are too short
                                elif len(tmpCandidate) >= 3:
                                    # else:
                                    individualMajorCandidates = [
                                        y for x in candidates for y in x
                                    ]
                                    activeQuery = pwcm.queryActiveSite(
                                        tmpCandidate, None
                                    )
                                    if activeQuery and len(activeQuery) > 0:
                                        otherMatches = [
                                            x
                                            for x in tmpCandidates[0]
                                            if x in activeQuery
                                        ]
                                        if any(
                                            [
                                                x
                                                for x in otherMatches
                                                if len(x) > len(tmpCandidate)
                                            ]
                                        ):
                                            continue
                                        activeCandidates.append(tmpCandidate)
                                    # enter modification information to self.database
                                    # logMess('INFO:SCT051', '{0}:Determined that {1} has an active site for modication'.format(reactant, tmpCandidate))
                                    # return [individualCandidate], unevenElements, candidates
                        if len(activeCandidates) > 0:
                            if len(activeCandidates) == 1:
                                logMess(
                                    "INFO:SCT051",
                                    "{0}:Determined through uniprot active site query that {1} has an active site for modication".format(
                                        reactant, activeCandidates[0]
                                    ),
                                )
                            if len(activeCandidates) > 1:
                                logMess(
                                    "WARNING:SCT151",
                                    "{0}:Determined through uniprot active site query that {1} have active site for modication. Defaulting to {2}".format(
                                        reactant, activeCandidates, activeCandidates[0]
                                    ),
                                )

                            for tmpCandidate, candidate in zip(
                                tmpCandidates, candidates
                            ):
                                fuzzyList = sbmlAnalyzer.processAdHocNamingConventions(
                                    reactant,
                                    candidate[0],
                                    {},
                                    False,
                                    dependencyGraph.keys(),
                                )
                                if len(fuzzyList) > 0 and fuzzyList[0][1]:
                                    if sbmlAnalyzer.testAgainstExistingConventions(
                                        fuzzyList[0][1],
                                        sbmlAnalyzer.namingConventions[
                                            "modificationList"
                                        ],
                                    ):
                                        self.database.eequivalenceTranslator2[
                                            fuzzyList[0][1]
                                        ].append(
                                            (
                                                activeCandidates[0],
                                                "{0}{1}".format(
                                                    activeCandidates, fuzzyList[0][1]
                                                ),
                                            )
                                        )
                                    else:
                                        self.database.eequivalenceTranslator2[
                                            fuzzyList[0][1]
                                        ] = [
                                            (
                                                activeCandidates[0],
                                                "{0}{1}".format(
                                                    activeCandidates[0], fuzzyList[0][1]
                                                ),
                                            )
                                        ]

                                    if (
                                        "{0}{1}".format(
                                            activeCandidates[0], fuzzyList[0][1]
                                        )
                                        not in dependencyGraph
                                    ):
                                        dependencyGraph[
                                            "{0}{1}".format(
                                                activeCandidates[0], fuzzyList[0][1]
                                            )
                                        ] = [[activeCandidates[0]]]

                                    for idx, element in enumerate(tmpCandidate):
                                        if element == activeCandidates[0]:
                                            tmpCandidates[0][idx] = "{0}{1}".format(
                                                activeCandidates[0], fuzzyList[0][1]
                                            )
                                            break
                                    return (
                                        [tmpCandidates[0]],
                                        unevenElements,
                                        candidates,
                                    )

                        if len(tmpCandidates) != 1:
                            if not self.database.softConstraints:
                                if loginformation:
                                    logMess(
                                        "ERROR:SCT213",
                                        "{0}:Atomizer needs user information to determine which element is being modified among components {1}={2}.".format(
                                            reactant, candidates, tmpCandidates
                                        ),
                                    )
                                # print self.database.userLabelDictionary
                                return None, None, None
                        else:

                            if not self.database.softConstraints:
                                if loginformation:
                                    modification = (
                                        sbmlAnalyzer.findMatchingModification(
                                            reactant, candidates[0][0]
                                        )
                                    )
                                    modification = (
                                        modification[0] if modification else "mod"
                                    )
                                    logMess(
                                        "ERROR:SCT212",
                                        "{1}:{0}:Atomizer needs user information to determine which element is being modified among component species:{2}:{3}".format(
                                            reactant,
                                            candidates[0],
                                            tmpCandidates[0],
                                            modification,
                                        ),
                                    )

                                return None, None, None

                        # return [tmpCandidates[0]], unevenElements

            elif len(tmpCandidates) > 1:
                # all candidates are equal/consistent
                if all(sorted(x) == sorted(tmpCandidates[0]) for x in tmpCandidates):
                    tmpCandidates = [tmpCandidates[0]]
                elif (
                    reactant in self.database.alternativeDependencyGraph
                    and loginformation
                ):
                    # candidates contradict each other but we have naming convention information in alternativeDependencyGraph
                    if not all(
                        sorted(x) == sorted(originalTmpCandidates[0])
                        for x in originalTmpCandidates
                    ):
                        if loginformation:
                            logMess(
                                "INFO:SCT001",
                                "{0}:Using lexical analysis since stoichiometry gives non-consistent information naming({1})!=stoichiometry({2})".format(
                                    reactant,
                                    self.database.alternativeDependencyGraph[reactant][
                                        0
                                    ],
                                    tmpCandidates,
                                ),
                            )

                    # else:
                    #    print self.database.alternativeDependencyGraph[reactant],tmpCandidates,reactant
                    #    logMess('INFO:Atomization', 'Using lexical analysis for species {0} =  {1} since stoichiometry gave conflicting information {2}'.format(reactant,
                    # self.database.alternativeDependencyGraph[reactant][0],
                    # tmpCandidates))

                    # fallback to naming conventions
                    candidate = self.database.alternativeDependencyGraph[reactant]
                    # resolve naming convention candidate to its basic components
                    # (molecule types)
                    namingTmpCandidates = selectBestCandidate(
                        reactant, [candidate[0]], dependencyGraph, sbmlAnalyzer
                    )[0]
                    if not namingTmpCandidates:
                        logMess(
                            "ERROR:SCT211",
                            "{0}:{1}:{2}:Cannot converge to solution, conflicting definitions".format(
                                reactant, tmpCandidates, originalTmpCandidates
                            ),
                        )
                        return None, None, None
                    if not any(
                        [
                            sorted(subcandidate) == sorted(namingTmpCandidates[0])
                            for subcandidate in tmpCandidates
                        ]
                    ):
                        if loginformation:
                            logMess(
                                "WARNING:SCT112",
                                "{0}:Stoichiometry analysis:{1}:results in non self-consistent definitions and conflicts with lexical analysis:{2}:Selecting lexical analysis".format(
                                    reactant, tmpCandidates, namingTmpCandidates
                                ),
                            )
                        atoAux.addAssumptions(
                            "lexicalVsstoch",
                            (
                                reactant,
                                ("lexical", str(namingTmpCandidates)),
                                ("stoch", str(tmpCandidates)),
                                ("original", str(originalTmpCandidates)),
                            ),
                            self.database.assumptions,
                        )

                    tmpCandidates = namingTmpCandidates
                    if loginformation:
                        self.database.alternativeDependencyGraph[
                            reactant
                        ] = tmpCandidates
                elif all(
                    sorted(x) == sorted(originalTmpCandidates[0])
                    for x in originalTmpCandidates
                ):
                    # the basic elements are the same but we are having trouble matching modifciations together
                    sortedCandidates = sorted(
                        [
                            ([y for y in x if y in reactant], i)
                            for i, x in enumerate(tmpCandidates)
                        ],
                        key=lambda z: [len(z[0]), sum([len(w) for w in z[0]])],
                        reverse=True,
                    )
                    if loginformation:
                        logMess(
                            "WARNING:SCT113",
                            "{0}:candidates:{1}:agree on the basic components but naming conventions cannot determine  specific modifications. Selecting:{2}:based on longest partial match".format(
                                reactant,
                                tmpCandidates,
                                tmpCandidates[sortedCandidates[0][1]],
                            ),
                        )
                    replacementCandidate = [tmpCandidates[sortedCandidates[0][1]]]
                    atoAux.addAssumptions(
                        "lexicalVsstoch",
                        (
                            reactant,
                            ("current", str(replacementCandidate)),
                            (
                                "alternatives",
                                str(
                                    [
                                        x
                                        for x in tmpCandidates
                                        if x != replacementCandidate[0]
                                    ]
                                ),
                            ),
                            ("original", str(originalTmpCandidates)),
                        ),
                        self.database.assumptions,
                    )
                    tmpCandidates = replacementCandidate
                else:
                    tmpCandidates2 = [
                        x
                        for x in tmpCandidates
                        if all(y not in x for y in self.database.constructedSpecies)
                    ]
                    # if we had constructed species disregard those since they are introducing noise
                    if len(tmpCandidates2) > 0 and len(tmpCandidates) != len(
                        tmpCandidates2
                    ):
                        return selectBestCandidate(
                            reactant, tmpCandidates2, dependencyGraph, sbmlAnalyzer
                        )
                    elif len(tmpCandidates2) == 0:
                        # the differences is between species that we created so its the LAE fault. Just choose one.
                        tmpCandidates.sort(key=len)
                        tmpCandidates = [tmpCandidates[0]]
                    else:
                        if loginformation:
                            logMess(
                                "ERROR:SCT211",
                                "{0}:{1}:{2}:Cannot converge to solution, conflicting definitions".format(
                                    reactant, tmpCandidates, originalTmpCandidates
                                ),
                            )
                        return None, None, None
            elif (
                reactant in self.database.alternativeDependencyGraph and loginformation
            ):
                # there is one stoichionetry candidate but the naming convention
                # and the stoichionetry dotn agree
                if (
                    tmpCandidates[0]
                    != self.database.alternativeDependencyGraph[reactant][0]
                ):
                    # make sure the naming convention is resolved to basic
                    # omponents
                    candidate = self.database.alternativeDependencyGraph[reactant]
                    # this is to avoid recursion
                    if loginformation:
                        del self.database.alternativeDependencyGraph[reactant]
                    namingtmpCandidates = selectBestCandidate(
                        reactant, [candidate[0]], dependencyGraph, sbmlAnalyzer
                    )[0]

                    # if they still disagree print error and use stoichiometry
                    if (
                        namingtmpCandidates
                        and tmpCandidates[0] != namingtmpCandidates[0]
                    ):

                        if loginformation:
                            if (
                                namingtmpCandidates[0][0]
                                in self.database.constructedSpecies
                            ):
                                namingTmpCandidates = tmpCandidates

                            else:
                                self.database.alternativeDependencyGraph[
                                    reactant
                                ] = namingtmpCandidates
                                logMess(
                                    "WARNING:SCT111",
                                    "{0}:stoichiometry analysis:{1}:conflicts with and naming conventions:{2}:Selecting lexical analysis".format(
                                        reactant,
                                        tmpCandidates,
                                        self.database.alternativeDependencyGraph[
                                            reactant
                                        ],
                                    ),
                                )
                        tmpCandidates = namingtmpCandidates
                        atoAux.addAssumptions(
                            "lexicalVsstoch",
                            (
                                reactant,
                                ("stoch", str(tmpCandidates)),
                                ("lexical", str(namingtmpCandidates)),
                                ("original", str(originalTmpCandidates)),
                            ),
                            self.database.assumptions,
                        )
                        for element in tmpCandidates[0]:
                            if element not in prunnedDependencyGraph:
                                # elemental species that were not used anywhere
                                # else but for those entries discovered through
                                # naming conventions
                                prunnedDependencyGraph[element] = []
                    elif not namingtmpCandidates:
                        if loginformation:
                            logMess(
                                "WARNING:SCT121",
                                "{0}:could not resolve naming({1}) into a viable compositional candidate. choosing stoichiometry({2})".format(
                                    reactant, candidate, tmpCandidates[0]
                                ),
                            )
            originalCandidateName = (
                candidateDict[tuple(tmpCandidates[0])]
                if tuple(tmpCandidates[0]) in candidateDict
                else None
            )
            return [tmpCandidates[0]], unevenElements, originalCandidateName

        prunnedDependencyGraph = deepcopy(dependencyGraph)

        tempMergedDependencyGraph = deepcopy(prunnedDependencyGraph)
        for element in self.database.alternativeDependencyGraph:
            if element in tempMergedDependencyGraph:
                tempMergedDependencyGraph[element].extend(
                    self.database.alternativeDependencyGraph[element]
                )
        weights = self.weightDependencyGraph(tempMergedDependencyGraph)

        # raise Exception

        unevenElementDict = {}
        for element in weights:
            candidates = [x for x in prunnedDependencyGraph[element[0]]]
            if len(candidates) == 1 and type(candidates[0][0]) == tuple:
                prunnedDependencyGraph[element[0]] = []
            if len(candidates) >= 1:
                candidates, uneven, originalCandidate = selectBestCandidate(
                    element[0], candidates, prunnedDependencyGraph, sbmlAnalyzer
                )
                # except CycleError:
                #    candidates = None
                #    uneven = []
                if uneven != []:
                    unevenElementDict[element[0]] = uneven
            if candidates is None:
                prunnedDependencyGraph[element[0]] = []
            else:
                prunnedDependencyGraph[element[0]] = [sorted(x) for x in candidates]

        weights = self.weightDependencyGraph(prunnedDependencyGraph)
        return prunnedDependencyGraph, weights, unevenElementDict, equivalenceTranslator

    @memoize
    def measureGraph(self, element, path):
        """
        Calculates the weight of individual paths as the sum of the weights of the individual candidates plus the number of
        candidates. The weight of an individual candidate is equal to the sum of strings contained in that candidate different
        from the original reactant
        >>> dummy = SCTSolver(None)
        >>> dummy.measureGraph('Trash',['0'])
        1
        >>> dummy.measureGraph('EGF',[['EGF']])
        2
        >>> dummy.measureGraph('EGFR_P',[['EGFR']])
        3
        >>> dummy.measureGraph('EGF_EGFR', [['EGF', 'EGFR']])
        4
        >>> dummy.measureGraph('A_B_C',[['A', 'B_C'], ['A_B', 'C']])
        7
        """
        counter = 1
        for x in path:
            if type(x) == list or type(x) == tuple:
                counter += self.measureGraph(element, x)
            elif x != "0" and x != element:
                counter += 1
        return counter

    # ASS: From my testing the iterative version is not only identical
    # but also significantly faster for most models since measure
    # graph doesn't get the same inputs, memoization doesn't pay off.
    def measureGraph2(self, element, path):
        """
        Identical to previous function but iterative instead of
        recursive
        """
        counter = 1
        if len(path) == 1:
            if type(path[0]) == list or type(path[0]) == tuple:
                counter += 1
                # check inside
                for x in path[0]:
                    if x != "0" and x != element:
                        counter += 1
            else:
                if path[0] != "0" and path[0] != element:
                    counter += 1
        else:
            # it's a longer thing
            counter += len(path)
            # flatten and check
            flat = [i for sb in path for i in sb if i]
            for x in flat:
                if x != "0" and x != element:
                    counter += 1
        return counter

    def weightDependencyGraph(self, dependencyGraph):
        """
        Given a dependency Graph it will return a list indicating the weights of its elements
        a path is calculated 
        >>> dummy = SCTSolver(None)
        >>> dummy.weightDependencyGraph({'EGF_EGFR_2':[['EGF_EGFR','EGF_EGFR']],'EGF_EGFR':[['EGF','EGFR']],'EGFR':[],'EGF':[],\
        'EGFR_P':[['EGFR']],'EGF_EGFR_2_P':[['EGF_EGFR_2']]})
        [['EGF', 2], ['EGFR', 2], ['EGFR_P', 4], ['EGF_EGFR', 5], ['EGF_EGFR_2', 9], ['EGF_EGFR_2_P', 10]]
        >>> dependencyGraph2 = {'A':[],'B':[],'C':[],'A_B':[['A','B']],'B_C':[['B','C']],'A_B_C':[['A_B','C'],['B_C','A']]}
        >>> dummy.weightDependencyGraph(dependencyGraph2)
        [['A', 2], ['C', 2], ['B', 2], ['B_C', 5], ['A_B', 5], ['A_B_C', 13]]
        """
        weights = []
        for element in dependencyGraph:
            path = self.resolveDependencyGraph(dependencyGraph, element)
            try:
                path2 = self.resolveDependencyGraph(dependencyGraph, element, True)
            except atoAux.CycleError:
                path2 = []
            # ASS: Swapping to iterative version of the function
            # weight = self.measureGraph(element, path) + len(path2)
            weight = self.measureGraph2(element, path) + len(path2)
            weights.append([element, weight])

        weights = sorted(weights, key=lambda rule: (rule[1], len(rule[0])))
        return weights

    # ASS: New method to make hashes from graphs. Some key points
    # 1) sorting is done to ensure same graph gives the same key, consistently
    # 2) python internal hashing function is used for the hashing
    # 3) should be very collision proof
    def make_key_from_graph(self, graph):
        hashable_tuples = []
        # If graph is empty just return the empty tuple result
        if len(graph) == 0:
            return marshal.dumps(hashable_tuples)
        # So we don't modify original graph
        tmpGraph = deepcopy(graph)
        # This turns the graph into a traditional graph implementation
        # where there are no edges that go to nodes that do not exist in the
        # graph, I'm making sure every node exists in the graph itself
        all_elems = set(
            [item[0] for sublist in tmpGraph.values() for item in sublist if item]
        )
        for elem in all_elems:
            try:
                a = tmpGraph[elem]
            except KeyError:
                tmpGraph[elem] = []
        # Now we should have a traditional graph implementation
        # I also want to unroll every element to turn this into a hashable
        # tuple of tuples type deal
        for key in sorted(tmpGraph):
            tmpGraph[key] = functools.reduce(
                lambda x, y: x + y, sorted(tmpGraph[key]), []
            )
        # Now we can turn this into a proper hashable object
        for key in sorted(tmpGraph):
            hashable_tuples.append((key, tuple(tmpGraph[key])))
        # Turn the list into tuples to it's hashable
        hashable_tuples = tuple(hashable_tuples)
        # return hash
        return hashable_tuples.__hash__()

    def resolveDependencyGraph(
        self, dependencyGraph, reactant, withModifications=False
    ):
        """
        Given a full species composition table and a reactant it will return an unrolled list of the molecule types
        (elements with no dependencies that define this reactant). The classification to the original candidates is lost
        since elements are fully unrolled. For getting dependencies keeping candidate consistency use consolidateDependencyGraph
        instead
        
        Args:
            withModifications (bool): returns a list of the 1:1 transformation relationships found in the path to this graph

        >>> dummy = SCTSolver(None)
        >>> dependencyGraph = {'EGF_EGFR_2':[['EGF_EGFR','EGF_EGFR']],'EGF_EGFR':[['EGF','EGFR']],'EGFR':[],'EGF':[],\
        'EGFR_P':[['EGFR']],'EGF_EGFR_2_P':[['EGF_EGFR_2']]}
        >>> dependencyGraph2 = {'A':[],'B':[],'C':[],'A_B':[['A','B']],'B_C':[['B','C']],'A_B_C':[['A_B','C'],['B_C','A']]}
        >>> dummy.resolveDependencyGraph(dependencyGraph, 'EGFR')
        [['EGFR']]
        >>> dummy.resolveDependencyGraph(dependencyGraph, 'EGF_EGFR')
        [['EGF'], ['EGFR']]
        >>> sorted(dummy.resolveDependencyGraph(dependencyGraph, 'EGF_EGFR_2_P'))
        [['EGF'], ['EGF'], ['EGFR'], ['EGFR']]
        
        >>> sorted(dummy.resolveDependencyGraph(dependencyGraph, 'EGF_EGFR_2_P', withModifications=True))
        [('EGF_EGFR_2', 'EGF_EGFR_2_P')]
        >>> sorted(dummy.resolveDependencyGraph(dependencyGraph2,'A_B_C'))
        [['A'], ['A'], ['B'], ['B'], ['C'], ['C']]
        """
        gkey = self.make_key_from_graph(dependencyGraph)
        try:
            self.dg = self.graph_map[gkey]
        except KeyError:
            self.graph_map[gkey] = dependencyGraph
            self.dg = dependencyGraph

        if self.memoizedResolver:
            topCandidate = self.resolveDependencyGraphHelper(
                gkey, reactant, [], withModifications
            )
        else:
            topCandidate = self.unMemoizedResolveDependencyGraphHelper(
                self.dg, reactant, [], withModifications
            )
        return topCandidate

    @memoizeMapped
    def resolveDependencyGraphHelper(
        self, gkey, reactant, memory, withModifications=False
    ):
        """
        Helper function for resolveDependencyGraph that adds a memory field to resolveDependencyGraphHelper to avoid 
        cyclical definitions problems 
        >>> dummy = SCTSolver(None)
        >>> dependencyGraph = {'EGF_EGFR_2':[['EGF_EGFR','EGF_EGFR']],'EGF_EGFR':[['EGF','EGFR']],'EGFR':[],'EGF':[],\
        'EGFR_P':[['EGFR']],'EGF_EGFR_2_P':[['EGF_EGFR_2']]}
        >>> dependencyGraph2 = {'A':[],'B':[],'C':[],'A_B':[['A','B']],'B_C':[['B','C']],'A_B_C':[['A_B','C'],['B_C','A']]}
        >>> sorted(dummy.resolveDependencyGraphHelper(dependencyGraph, 'EGF_EGFR_2_P',[]))
        [['EGF'], ['EGF'], ['EGFR'], ['EGFR']]
       
        >>> sorted(dummy.resolveDependencyGraphHelper(dependencyGraph, 'EGF_EGFR_2_P', [], withModifications=True))
        [('EGF_EGFR_2', 'EGF_EGFR_2_P')]

        >>> sorted(dummy.resolveDependencyGraphHelper(dependencyGraph2, 'A_B_C', []))
        [['A'], ['A'], ['B'], ['B'], ['C'], ['C']]

        >>> dependencyGraph3 = {'C1': [['C2']],'C2':[['C3']],'C3':[['C1']]}
        >>> resolveDependencyGraphHelper(dummy.dependencyGraph3, 'C3', [], withModifications=True)
        Traceback (innermost last):
          File "<stdin>", line 1, in ?
        CycleError
        """

        result = []
        # if type(reactant) == tuple:
        #    return []
        if (
            reactant not in self.dg
            or self.dg[reactant] == []
            or self.dg[reactant] == [[reactant]]
        ):
            if not withModifications:
                result.append([reactant])
        else:
            for option in self.dg[reactant]:
                tmp = []
                for element in option:
                    if element in memory and not withModifications:
                        result.append([element])
                        continue
                    elif element in memory:
                        # logMess(
                        #    'ERROR:SCT201', 'dependency cycle detected on {0}'.format(element))
                        raise atoAux.CycleError(memory)
                    baseElement = self.resolveDependencyGraphHelper(
                        gkey, element, memory + [element], withModifications
                    )
                    if baseElement is not None:
                        tmp.extend(baseElement)
                # if not withModifications:
                result.extend(tmp)
                if len(option) == 1 and withModifications and option[0] != reactant:
                    result.append((option[0], reactant))
        return result

    def unMemoizedResolveDependencyGraphHelper(
        self, dependencyGraph, reactant, memory, withModifications=False
    ):
        """
        Helper function for resolveDependencyGraph that adds a memory field to resolveDependencyGraphHelper to avoid 
        cyclical definitions problems 
        >>> dummy = SCTSolver(None)
        >>> dependencyGraph = {'EGF_EGFR_2':[['EGF_EGFR','EGF_EGFR']],'EGF_EGFR':[['EGF','EGFR']],'EGFR':[],'EGF':[],\
        'EGFR_P':[['EGFR']],'EGF_EGFR_2_P':[['EGF_EGFR_2']]}
        >>> dependencyGraph2 = {'A':[],'B':[],'C':[],'A_B':[['A','B']],'B_C':[['B','C']],'A_B_C':[['A_B','C'],['B_C','A']]}
        >>> sorted(dummy.resolveDependencyGraphHelper(dependencyGraph, 'EGF_EGFR_2_P',[]))
        [['EGF'], ['EGF'], ['EGFR'], ['EGFR']]
       
        >>> sorted(dummy.resolveDependencyGraphHelper(dependencyGraph, 'EGF_EGFR_2_P', [], withModifications=True))
        [('EGF_EGFR_2', 'EGF_EGFR_2_P')]

        >>> sorted(dummy.resolveDependencyGraphHelper(dependencyGraph2, 'A_B_C', []))
        [['A'], ['A'], ['B'], ['B'], ['C'], ['C']]

        >>> dependencyGraph3 = {'C1': [['C2']],'C2':[['C3']],'C3':[['C1']]}
        >>> resolveDependencyGraphHelper(dummy.dependencyGraph3, 'C3', [], withModifications=True)
        Traceback (innermost last):
          File "<stdin>", line 1, in ?
        CycleError
        """

        result = []
        # if type(reactant) == tuple:
        #    return []
        if (
            reactant not in dependencyGraph
            or dependencyGraph[reactant] == []
            or dependencyGraph[reactant] == [[reactant]]
        ):
            if not withModifications:
                result.append([reactant])
        else:
            for option in dependencyGraph[reactant]:
                tmp = []
                for element in option:
                    if element in memory and not withModifications:
                        result.append([element])
                        continue
                    elif element in memory:
                        # logMess(
                        #    'ERROR:SCT201', 'dependency cycle detected on {0}'.format(element))
                        raise atoAux.CycleError(memory)
                    baseElement = self.unMemoizedResolveDependencyGraphHelper(
                        dependencyGraph, element, memory + [element], withModifications
                    )
                    if baseElement is not None:
                        tmp.extend(baseElement)
                # if not withModifications:
                result.extend(tmp)
                if len(option) == 1 and withModifications and option[0] != reactant:
                    result.append((option[0], reactant))
        return result
