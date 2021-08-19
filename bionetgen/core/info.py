class BNGInfo:
    def __init__(self, config, args=None):
        self.config = config
        self.args = args

    def gatherInfo(self):
        import subprocess
        import os
        import bionetgen
        import numpy
        import pandas
        import roadrunner

        self.info = {}

        # Get BNG version
        with open(os.path.join(*["bionetgen", "assets", "BNGVERSION"]), "r") as f:
            read_data = f.read()
        self.info["BNG version"] = read_data[10:15]

        # Get CLI version
        with open(os.path.join(*["bionetgen", "assets", "VERSION"]), "r") as f:
            read_data = f.read()
        self.info["CLI version"] = read_data

        # Get BNG2.pl path
        self.info["BNG2.pl path"] = self.config.get("bionetgen", "bngpath")

        # Get pyBNG path
        # IPython, os.path
        self.info["pyBNG path"] = ""

        # Get Perl version
        # Read in CLI text
        result = subprocess.run(["perl", "-v"], stdout=subprocess.PIPE)
        text = str(result.stdout)
        # Find start & end indices
        num_start = text.find("(v") + 2
        num_end = text.find(")")
        # Save version info
        self.info["Perl version"] = text[num_start:num_end]

        # Get numpy version #
        self.info["numpy version"] = numpy.version.version

        # Get pandas version
        self.info["pandas version"] = pandas.__version__

        # Get libRoadRunner version
        text = roadrunner.getVersionStr()
        self.info["libRoadRunner version"] = text[0:5]

        return self.info

    def messageGeneration(self):
        self.message = " "
        message_lines = []

        for key in self.info:
            text = str(key + ": " + self.info[key] + "\n")
            message_lines.append(text)

        self.message = "".join((message_lines))

        return self.message

    def run(self):
        print(self.message)
