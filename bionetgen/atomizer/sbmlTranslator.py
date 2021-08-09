# -*- coding: utf-8 -*-
"""
Created on Tue May 21 12:38:21 2013

@author: proto
"""

import libsbml2bngl as ls2b
import argparse
import yaml


def defineConsole():
    parser = argparse.ArgumentParser(description="SBML to BNGL translator")
    parser.add_argument(
        "-i", "--input-file", type=str, help="input SBML file", required=True
    )
    parser.add_argument(
        "-t", "--annotation", action="store_true", help="keep annotation information"
    )
    parser.add_argument("-o", "--output-file", type=str, help="output SBML file")
    parser.add_argument("-c", "--convention-file", type=str, help="Conventions file")
    parser.add_argument(
        "-n", "--naming-conventions", type=str, help="Naming conventions file"
    )
    parser.add_argument(
        "-u", "--user-structures", type=str, help="User defined species"
    )
    parser.add_argument(
        "-id",
        "--molecule-id",
        action="store_true",
        help="use SBML molecule ids instead of names. IDs are less descriptive but more bngl friendly. Use only if the generated BNGL has syntactic errors",
    )
    parser.add_argument(
        "-cu",
        "--convert-units",
        action="store_false",
        help="convert units. Otherwise units are copied straight from sbml to bngl",
    )
    parser.add_argument(
        "-a", "--atomize", action="store_true", help="Infer molecular structure"
    )
    parser.add_argument(
        "-p",
        "--pathwaycommons",
        action="store_true",
        help="Use pathway commons to infer molecule binding. This setting requires an internet connection and will query the pathway commons web service.",
    )
    parser.add_argument(
        "-b",
        "--bionetgen-analysis",
        type=str,
        help="Set the BioNetGen path for context post analysis.",
    )
    parser.add_argument(
        "-s",
        "--isomorphism-check",
        action="store_true",
        help="disallow atomizations that produce the same graph structure",
    )
    parser.add_argument(
        "-I",
        "--ignore",
        action="store_true",
        help="ignore atomization translation errors",
    )
    parser.add_argument(
        "-mr",
        "--memoized-resolver",
        default=False,
        action="store_true",
        help="sometimes the dependency graph is too large and might cause a very large memory requirement. This option will slow the translator down but will decrease memory usage",
    )
    parser.add_argument(
        "-k",
        "--keep-local-parameters",
        default=False,
        action="store_true",
        help="this option will keep the local parameters unresolved so that they can be controlled from the parameter section in the BNGL. Without this option, local parameters will be resolved to their values in functions",
    )
    parser.add_argument(
        "-q",
        "--quiet-mode",
        default=False,
        action="store_true",
        help="this option will supress logging into STDIO and instead will write the logging into a file",
    )
    parser.add_argument(
        "-ll",
        "--log-level",
        default="DEBUG",
        help='This option allows you to select a logging level, from quietest to loudest options are: "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG". Default is set to DEBUG',
    )

    return parser


def checkInput(namespace):
    options = {}
    options["inputFile"] = namespace.input_file

    conv, useID, naming = ls2b.selectReactionDefinitions(options["inputFile"])
    options["outputFile"] = (
        namespace.output_file
        if namespace.output_file is not None
        else options["inputFile"] + ".bngl"
    )
    options["conventionFile"] = (
        namespace.convention_file if namespace.convention_file is not None else conv
    )
    options["userStructure"] = namespace.user_structures
    options["namingConventions"] = (
        namespace.naming_conventions
        if namespace.naming_conventions is not None
        else naming
    )
    options["useId"] = namespace.molecule_id
    options["annotation"] = namespace.annotation
    options["atomize"] = namespace.atomize
    options["pathwaycommons"] = namespace.pathwaycommons
    options["bionetgenAnalysis"] = namespace.bionetgen_analysis
    options["isomorphismCheck"] = namespace.isomorphism_check
    options["ignore"] = namespace.ignore
    options["noConversion"] = namespace.convert_units
    options["memoizedResolver"] = namespace.memoized_resolver
    options["replaceLocParams"] = not namespace.keep_local_parameters
    options["quietMode"] = namespace.quiet_mode
    assert namespace.log_level in [
        "CRITICAL",
        "ERROR",
        "WARNING",
        "INFO",
        "DEBUG",
    ], "Logging level {} is not an allowed level".format(namespace.log_level)
    options["logLevel"] = namespace.log_level
    return options


def main():
    parser = defineConsole()
    namespace = parser.parse_args()

    options = checkInput(namespace)
    returnArray = ls2b.analyzeFile(
        options["inputFile"],
        options["conventionFile"],
        options["useId"],
        options["namingConventions"],
        options["outputFile"],
        speciesEquivalence=options["userStructure"],
        atomize=options["atomize"],
        bioGrid=False,
        pathwaycommons=options["pathwaycommons"],
        ignore=options["ignore"],
        noConversion=options["noConversion"],
        memoizedResolver=options["memoizedResolver"],
        replaceLocParams=options["replaceLocParams"],
        quietMode=options["quietMode"],
        logLevel=options["logLevel"],
    )

    if namespace.bionetgen_analysis and returnArray:
        ls2b.postAnalyzeFile(
            options["outputFile"],
            namespace.bionetgen_analysis,
            returnArray.database,
            replaceLocParams=options["replaceLocParams"],
        )

    if namespace.annotation and returnArray:
        with open(options["outputFile"] + ".yml", "w") as f:
            f.write(yaml.dump(returnArray.annotation, default_flow_style=False))


if __name__ == "__main__":
    main()
