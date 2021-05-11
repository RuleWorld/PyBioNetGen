from bionetgen.main import BioNetGen
from .utils import find_BNG_path

# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config['bionetgen']
def_bng_path = conf['bngpath']

class BNGFile:
    def __init__(self, path, BNGPATH=def_bng_path) -> None:
        self.path = path
        
        BNGPATH, bngexec = find_BNG_path(BNGPATH)
        self.BNGPATH = BNGPATH
        self.bngexec = bngexec 
        