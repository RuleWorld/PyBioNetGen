from bionetgen.core.utils.logging import BNGLogger


class BNGInfo:
    """
    Used by the Cement app to execute the info subcommand, which involves gathering, preparing, and printing
    relevant version and path information.

    The gatherInfo() method finds and stores all necessary information.
    The messageGeneration() method prepares this information in a text string.
    The run() method simply outputs all the information.

    Requires a configuration file. An additional set of arguments are optional.
    """

    def __init__(self, config, args=None, app=None):
        self.config = config
        self.args = args
        self.app = app
        self.logger = BNGLogger(app=self.app)

    def gatherInfo(self):
        """
        Gathers information about relevant versions and paths into a dictionary.
        """
        import subprocess
        import os
        import bionetgen
        import numpy
        import pandas
        import roadrunner

        self.logger.debug("Gathering info", loc=f"{__file__} : BNGInfo.gatherInfo()")

        self.info = {}

        # Add some description for the following information
        self.info["\nThe following are related to BioNetGen and its execution"] = ""

        self.logger.debug("BNG info", loc=f"{__file__} : BNGInfo.gatherInfo()")
        # Get BNG version
        with open(
            os.path.join(
                *[os.path.dirname(bionetgen.__file__), "assets", "BNGVERSION"]
            ),
            "r",
        ) as f:
            read_data = f.read()
        self.info["BNG version"] = read_data[10:15]

        # Get BNG2.pl path
        self.info["BNG2.pl path"] = (
            self.config.get("bionetgen", "bngpath") + " (the main executable for BNG)"
        )

        self.logger.debug("Perl info", loc=f"{__file__} : BNGInfo.gatherInfo()")
        # Get Perl version
        # Read in CLI text
        result = subprocess.run(["perl", "-v"], stdout=subprocess.PIPE)
        text = str(result.stdout)
        # Find start & end indices
        num_start = text.find("(v") + 2
        num_end = text.find(")")
        # Save version info
        self.info["Perl version"] = text[num_start:num_end] + " (used to run BNG2.pl)"

        self.logger.debug("PyBNG info", loc=f"{__file__} : BNGInfo.gatherInfo()")
        # Get CLI version
        with open(
            os.path.join(*[os.path.dirname(bionetgen.__file__), "assets", "VERSION"]),
            "r",
        ) as f:
            read_data = f.read()
        self.info["CLI version"] = read_data

        # Get pyBNG path
        self.info["pyBNG path"] = (
            os.path.dirname(bionetgen.__file__) + " (the PyBNG installation)"
        )

        self.logger.debug(
            "Info on installed python libraries",
            loc=f"{__file__} : BNGInfo.gatherInfo()",
        )

        # Add some description for the following information
        self.info["\nThe following libraries are required by PyBioNetGen"] = ""

        # Get numpy version
        self.info["numpy version"] = numpy.version.version

        # Get pandas version
        self.info["pandas version"] = pandas.__version__

        # Get libRoadRunner version
        text = roadrunner.getVersionStr()
        self.info["libRoadRunner version"] = text[0:5]

        return self.info

    def messageGeneration(self):
        """
        Takes the dictionary created by gatherInfo() and
        converts it to a string of text for printing.
        """
        self.logger.debug(
            "Generating message", loc=f"{__file__} : BNGInfo.messageGeneration()"
        )

        self.message = " "

        # Create lines of message using self.info dictionary
        message_lines = []

        for key in self.info:
            text = str(key + ": " + self.info[key] + "\n")
            message_lines.append(text)
        # Join lines to create entire message
        self.message = "".join((message_lines))

        return self.message

    def run(self):
        """
        Simply prints out the created information message.
        """
        self.logger.debug("Printing message", loc=f"{__file__} : BNGInfo.run()")

        print(self.message)
