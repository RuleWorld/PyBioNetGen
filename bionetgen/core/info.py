class BNGInfo:
    def __init__(self, config, args):
        return

    def gatherInfo(self):
        import subprocess
        import os
        import platform

        self.info = {}

        # Get BNG version # Note: could use subprocess 'bionetgen -v'
        with open(
            os.path.join(*["bionetgen", "assets", "BNGVERSION"]), "r"
        ) as f:  # 'PyBioNetGen/bionetgen/assets/BNGVERSION'
            read_data = f.read()
        self.info["BNG version"] = read_data[10:15]

        # Get CLI version # Note: could use subprocess 'bionetgen -v'
        with open(
            os.path.join(*["bionetgen", "assets", "VERSION"]), "r"
        ) as f:  # 'PyBioNetGen/bionetgen/assets/VERSION'
            read_data = f.read()
        self.info["CLI version"] = read_data  # TODO: add decimals to version num?

        # # Get BNG2.pl path
        # # Determine OS
        # get_os = platform.system
        # # Get path based on OS
        # if get_os == 'Windows':
        #     #os.path.join(*["bionetgen", "bng-win", "BNG2.pl"]), "r")
        #     pass

        # elif get_os == 'Darwin':
        #     with open(os.path.join(*["bionetgen", "bng-mac", "BNG2.pl"]), "r") as f:
        #         read_data = f.read()
        #     self.info['BNG2.pl path'] = read_data[1:2]
        # elif get_os == 'Linux':
        #     with open(os.path.join(*["bionetgen", "bng-linux", "BNG2.pl"]), "r") as f:
        #         read_data = f.read()
        #     self.info["BNG2.pl path"] = read_data[1:2]
        # else:
        #     pass

        # Get pyBNG path
        # Read in CLI text
        result = subprocess.run(["pip", "show", "bionetgen"], stdout=subprocess.PIPE)
        text = str(result.stdout)
        # Find start & end indices
        num_start = text.find("Location") + 10
        num_end = text.find("Requires") - 4
        # Save path info
        self.info["pyBNG path"] = text[num_start:num_end]

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
        # Read in CLI text
        result = subprocess.run(["pip", "show", "numpy"], stdout=subprocess.PIPE)
        text = str(result.stdout)
        # Find start & end indices
        num_start = text.find("Version") + 9
        num_end = text.find("Summary") - 4
        # Save version info
        self.info["numpy version"] = text[num_start:num_end]

        # Get pandas version
        # Read in CLI text
        result = subprocess.run(["pip", "show", "pandas"], stdout=subprocess.PIPE)
        text = str(result.stdout)
        # Find start & end indices
        num_start = text.find("Version") + 9
        num_end = text.find("Summary") - 4
        # Save version info
        self.info["pandas version"] = text[num_start:num_end]

        # Get libRoadRunner version
        # Read in CLI text
        result = subprocess.run(["pip", "show", "pandas"], stdout=subprocess.PIPE)
        text = str(result.stdout)
        # Find start & end indices
        num_start = text.find("Version") + 9
        num_end = text.find("Summary") - 4
        # Save version info
        self.info["libRoadRunner version"] = text[num_start:num_end]

        return self.info

    def messageGeneration(self):
        self.message = " "
        message_lines = []

        for key in self.info:
            text = str(key + ": " + self.info[key] + "\n")
            message_lines.append(text)

        self.message = " ".join((message_lines))

        return self.message

    def run(self):
        print(self.message)
