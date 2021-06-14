import platform, os, subprocess
from cement import init_defaults
from cement.utils.version import get_version_banner
from .version import get_version
import urllib.request, json


def get_latest_bng_version():
    # get the version tag for the BNG version used
    libpath = os.path.abspath(__file__)
    libpath = libpath.split(os.path.sep)
    verpath = os.path.sep.join(libpath[:-2] + ["assets", "BNGVERSION"])
    if os.path.isfile(verpath):
        with open(verpath) as f:
            tag = f.read()
        return tag
    else:
        return "UNKNOWN"


class BNGDefaults:
    def __init__(self):
        """
        A class to define the default configuration for cement apps

        Attributes
        ----------
        system : str
            the name of the OS that's running the app
        bng_name : str
            OS appropriate name of the BNG folder
        bng_path : str
            full absolute path to the BNG folder
        lib_path : str
            path to CLI library
        stdout : str
            the name of the subprocess attribute to pass stdout to
        stderr : str
            the name of the subprocess attribute to pass stderr to
        config : dict
            dictionary containing the application defaults
        banner : str
            app banner that gets printed when ran with -v
        """
        # determine what bng we are using
        system = platform.system()
        if system == "Linux":
            bng_name = "bng-linux"
        elif system == "Windows":
            bng_name = "bng-win"
        elif system == "Darwin":
            bng_name = "bng-mac"
        # set attributes
        self.system = system
        self.bng_name = bng_name
        # configuration defaults
        CONFIG = init_defaults("bionetgen")
        lib_path = os.path.dirname(__file__)
        lib_path = os.path.split(lib_path)[0]
        CONFIG["bionetgen"]["bngpath"] = os.path.join(lib_path, bng_name)
        CONFIG["bionetgen"]["notebook"] = {}
        CONFIG["bionetgen"]["notebook"]["path"] = os.path.join(
            lib_path, "assets", "bionetgen.ipynb"
        )
        CONFIG["bionetgen"]["notebook"]["template"] = os.path.join(
            lib_path, "assets", "bionetgen-temp.ipynb"
        )
        CONFIG["bionetgen"]["notebook"]["name"] = "bng-notebook.ipynb"
        # set attributes
        self.bng_path = os.path.join(lib_path, bng_name)
        self.lib_path = lib_path
        # version banner
        VERSION_BANNER = """BioNetGen simple command line interface {}\nBioNetGen version: {}\n{}
        """.format(
            get_version(), get_latest_bng_version(), get_version_banner()
        )
        # set attributes
        self.banner = VERSION_BANNER
        # stdout
        CONFIG["bionetgen"]["stdout"] = "PIPE"
        CONFIG["bionetgen"]["stderr"] = "STDOUT"
        self.stdout = subprocess.PIPE
        self.stderr = subprocess.PIPE
        self.config = CONFIG


defaults = BNGDefaults()
