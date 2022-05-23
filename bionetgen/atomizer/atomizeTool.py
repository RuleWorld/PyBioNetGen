import bionetgen.atomizer.libsbml2bngl as ls2b
from bionetgen.core.defaults import BNGDefaults
import yaml, os

from bionetgen.core.utils.logging import BNGLogger, log_level


d = BNGDefaults()


class AtomizeTool:
    def __init__(
        self, input_file=None, options_dict=None, parser_namespace=None, app=None
    ):
        self.app = app
        self.logger = BNGLogger(app=self.app)
        self.logger.debug(
            "Setting up AtomizeTool object", loc=f"{__file__} : AtomizeTool.__init__()"
        )
        # we generate our defaults first and override it with
        # the dictionary first and then the namespace
        config = {
            "input": None,  # we need this, check at the end and fail if we don't have it
            "annotation": False,
            "output": None,
            "convention_file": None,
            "naming_conventions": None,
            "user_structures": None,
            "molecule_id": False,
            "convert_units": False,  # currently not supported
            "atomize": False,  # default is flat translation
            "pathwaycommons": True,  # requires connection so default is false
            "bionetgen_analysis": os.path.join(
                d.bng_path, "BNG2.pl"
            ),  # TODO: get it from app config
            "isomorphism_check": False,  # wtf do we do here?
            "ignore": False,  # wtf do we do here?
            "memoized_resolver": False,
            "keep_local_parameters": False,
            "quiet_mode": False,
            "obs_map_file": None,
            "log_level": "DEBUG",  # options are "CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"
        }
        # input file
        if input_file is not None:
            config["input"] = input_file
        # dictionary override
        if options_dict is not None:
            for key in config:
                if key in options_dict:
                    config[key] = options_dict[key]
        # namespace override
        if parser_namespace is not None:
            for key in config:
                if hasattr(parser_namespace, key):
                    config[key] = getattr(parser_namespace, key)
        # special handling of log level
        if log_level is not None:
            config["log_level"] = log_level
        elif self.app is not None:
            # we called this from the CLI
            if self.app.pargs.debug:
                config["log_level"] = "DEBUG"
            elif self.app.pargs.log_level is not None:
                config["log_level"] = self.app.pargs.log_level
            else:
                # we called the CLI but didn't give any log_level info
                config["log_level"] = "INFO"
        else:
            # we called from library but no log_level info exists
            config["log_level"] = "INFO"

        # check config options
        self.config = self.checkConfig(config)

    def checkConfig(self, config):
        self.logger.debug(
            "Validating config options", loc=f"{__file__} : AtomizeTool.checkConfig()"
        )
        options = {}
        options["inputFile"] = config["input"]  # TODO: ensure this is not None
        conv, useID, naming = ls2b.selectReactionDefinitions(options["inputFile"])
        options["outputFile"] = (
            config["output"]
            if config["output"] is not None
            else options["inputFile"] + ".bngl"
        )
        options["conventionFile"] = (
            config["convention_file"] if config["convention_file"] is not None else conv
        )
        options["userStructure"] = config["user_structures"]
        options["namingConventions"] = (
            config["naming_conventions"]
            if config["naming_conventions"] is not None
            else naming
        )
        options["useId"] = config["molecule_id"]
        options["annotation"] = config["annotation"]
        options["atomize"] = config["atomize"]
        options["pathwaycommons"] = config["pathwaycommons"]
        options["bionetgenAnalysis"] = config["bionetgen_analysis"]
        options["isomorphismCheck"] = config["isomorphism_check"]
        options["ignore"] = config["ignore"]
        options["noConversion"] = not config["convert_units"]
        options["memoizedResolver"] = config["memoized_resolver"]
        options["replaceLocParams"] = not config["keep_local_parameters"]
        options["quietMode"] = config["quiet_mode"]
        options["obs_map_file"] = config["obs_map_file"]
        assert config["log_level"] in [
            "CRITICAL",
            "ERROR",
            "WARNING",
            "INFO",
            "DEBUG",
        ], "Logging level {} is not an allowed level".format(config["log_level"])
        options["logLevel"] = config["log_level"]
        return options

    def run(self):
        # TODO: Make atomizer also use cement app logging
        # this involves changing a lot of code in atomizer!
        self.logger.debug("Analyzing SBML file", loc=f"{__file__} : AtomizeTool.run()")
        self.returnArray = ls2b.analyzeFile(
            self.config["inputFile"],
            self.config["conventionFile"],
            self.config["useId"],
            self.config["namingConventions"],
            self.config["outputFile"],
            speciesEquivalence=self.config["userStructure"],
            atomize=self.config["atomize"],
            bioGrid=False,
            pathwaycommons=self.config["pathwaycommons"],
            ignore=self.config["ignore"],
            noConversion=self.config["noConversion"],
            memoizedResolver=self.config["memoizedResolver"],
            replaceLocParams=self.config["replaceLocParams"],
            quietMode=self.config["quietMode"],
            logLevel=self.config["logLevel"],
            obs_map_file=self.config["obs_map_file"],
            app=self.app,
        )
        self.logger.debug("Post-analysis", loc=f"{__file__} : AtomizeTool.run()")
        try:
            if self.config["bionetgenAnalysis"] and self.returnArray:
                ls2b.postAnalyzeFile(
                    self.config["outputFile"],
                    self.config["bionetgenAnalysis"],
                    self.returnArray.database,
                    replaceLocParams=self.config["replaceLocParams"],
                    obs_map_file=self.config["obs_map_file"],
                )
        except Exception as e:
            self.logger.warning(
                "Post-analysis failed", loc=f"{__file__} : AtomizeTool.run()"
            )
            print("Post analysis failed")
            print(e)

        self.logger.debug(
            "Writing annotation file", loc=f"{__file__} : AtomizeTool.run()"
        )

        try:
            if self.config["annotation"] and self.returnArray:
                with open(self.config["outputFile"] + ".yml", "w") as f:
                    f.write(
                        yaml.dump(self.returnArray.annotation, default_flow_style=False)
                    )
        except Exception as e:
            self.logger.warning(
                "Failed to write annotation file", loc=f"{__file__} : AtomizeTool.run()"
            )
            print(e)
        return self.returnArray
