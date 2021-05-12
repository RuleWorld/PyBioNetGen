import bionetgen as bng
import subprocess, os, xmltodict, sys

from bionetgen.main import BioNetGen
from .utils import find_BNG_path
from tempfile import TemporaryDirectory
from tempfile import TemporaryFile

# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config['bionetgen']
def_bng_path = conf['bngpath']

class BNGFile:
    '''
    File object designed to deal with .bngl file manipulations. 

    Usage: BNGFile(bngl_path)
           BNGFile(bngl_path, BNGPATH)

    Attributes
    ----------

    
    Methods
    -------
    
    '''
    def __init__(self, path, BNGPATH=def_bng_path) -> None:
        self.path = path
        self._action_list = ["generate_network(", "generate_hybrid_model(","simulate(", 
            "simulate_ode(", "simulate_ssa(", "simulate_pla(", "simulate_nf(", 
            "parameter_scan(", "bifurcate(", "readFile(", "writeFile(", "writeModel(", 
            "writeNetwork(", "writeXML(", "writeSBML(", "writeMfile(", "writeMexfile(", 
            "writeMDL(", "visualize(", "setConcentration(", "addConcentration(", 
            "saveConcentration(", "resetConcentrations(", "setParameter(", "saveParameters(", 
            "resetParameters(", "quit(", "setModelName(", "substanceUnits(", "version(", 
            "setOption("]
        BNGPATH, bngexec = find_BNG_path(BNGPATH)
        self.BNGPATH = BNGPATH
        self.bngexec = bngexec 
    
    def generate_xml(self, xml_file, model_file=None) -> bool:
        '''
        '''
        if model_file is None:
            model_file = self.path
            
        cur_dir = os.getcwd()
        # temporary folder to work in
        with TemporaryDirectory() as temp_folder:
            # make a stripped copy without actions in the folder
            stripped_bngl = self.strip_actions(model_file, temp_folder)
            # run with --xml 
            os.chdir(temp_folder)
            # TODO: take stdout option from app instead
            rc = subprocess.run(["perl",self.bngexec, "--xml", stripped_bngl], stdout=bng.defaults.stdout)
            if rc.returncode == 1:
                print("XML generation failed")
                # go back to our original location
                os.chdir(cur_dir)
                # shutil.rmtree(temp_folder)
                return False
            else:
                # we should now have the XML file 
                path, model_name = os.path.split(stripped_bngl)
                model_name = model_name.replace(".bngl", "")
                written_xml_file = model_name + ".xml"
                # import ipdb;ipdb.set_trace()
                with open(written_xml_file, "r") as f:
                    content = f.read()
                    xml_file.write(content)
                # since this is an open file, to read it later
                # we need to go back to the beginning
                xml_file.seek(0)
                # go back to our original location
                os.chdir(cur_dir)
                return True

    def strip_actions(self, model_path, folder) -> str:
        '''
        Strips actions from a BNGL file and makes a copy
        into the given folder
        '''
        # Get model name and setup path stuff
        path, model_file = os.path.split(model_path)
        # open model and strip actions
        with open(model_path, 'r') as mf:
            # read and strip actions
            mlines = mf.readlines()
            stripped_lines = filter(lambda x: self._not_action(x), mlines)
        # TODO: read stripped lines and store the actions
        # open new file and write just the model
        stripped_model = os.path.join(folder, model_file)
        with open(stripped_model, 'w') as sf:
            sf.writelines(stripped_lines)
        return stripped_model 

    def _not_action(self, line) -> bool:
        for action in self._action_list:
            if action in line:
                return False
        return True