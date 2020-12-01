import platform, os, subprocess
from cement import init_defaults
from cement.utils.version import get_version_banner
from .version import get_version

class BNGDefaults:
    def __init__(self):
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
        CONFIG = init_defaults('bionetgen')
        lib_path = os.path.dirname(__file__)
        lib_path = os.path.split(lib_path)[0]
        CONFIG['bionetgen']['bngpath'] = os.path.join(lib_path, bng_name)
        CONFIG['bionetgen']['notebook'] = {}
        CONFIG['bionetgen']['notebook']["path"] = os.path.join(lib_path, "assets", "bionetgen.ipynb")
        CONFIG['bionetgen']['notebook']["template"] = os.path.join(lib_path, "assets", "bionetgen-temp.ipynb")
        CONFIG["bionetgen"]["notebook"]["name"] = "bng-notebook.ipynb"
        # set attributes
        self.bng_path = os.path.join(lib_path, bng_name)
        self.lib_path = lib_path
        self.config = CONFIG
        # version banner
        VERSION_BANNER= """
        BioNetGen simple command line interface {}
        {}
        """.format(get_version(), get_version_banner())
        # set attributes
        self.banner = VERSION_BANNER
        # stdout
        self.stdout = subprocess.PIPE

defaults = BNGDefaults()
