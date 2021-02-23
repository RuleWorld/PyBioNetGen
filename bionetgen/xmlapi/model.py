import bionetgen as bng
from bionetgen.main import BioNetGen
import re, functools, subprocess, os, xmltodict, sys, shutil, tempfile
from tempfile import TemporaryDirectory
from tempfile import TemporaryFile
from .utils import find_BNG_path
from .structs import Parameters, Species, MoleculeTypes, Observables, Functions, Compartments, Rules, Actions

# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config['bionetgen']
def_bng_path = conf['bngpath']

###### CORE OBJECT AND PARSING FRONT-END ######
class bngmodel:
    '''
    Main model object and entry point for XMLAPI. The goal of this 
    object is to generate and read the BNGXML of a given BNGL model
    and give the user a pythonic interface to the resulting model object. 

    TODO: * Make model object Cement app configuration aware
    * disentangle XML generation and the model object itself
    * disentangle simulator handling from the model object
    
    Usage: bngmodel(bng_model)
           bngmodel(bng_model, BNGPATH)

    Attributes
    ----------
    active_blocks : list[str]
        a list of the blocks that have been parsed in the model
    _action_list : list[str]
        a list of approved actions
    BNGPATH : str
        path to bionetgen where BNG2.pl lives
    bngexec : str
        path to BNG2.pl
    model_name : str
        name of the model, generally set from the given BNGL file
    recompile : bool
        a tag to keep track if any changes have been made to the model
        via the XML API by the user
    changes : dict
        a list of changes the user have made to the model
    
    Methods
    -------
    parse_model(model_file)
        parses the BNGL model at the given path model_file
    reset_compilation_tags()
        resets compilation tags of each block to keep track of any changes the user
        makes to the model via the API
    generate_xml(model_file, xml_file)
        this generates the BNGXML of the given model file in the xml_file argument
        given
    strip_actions(model_path, folder)
        strips actions from the given model in model_path and writes a model without
        actions in the folder given
    parse_xml(xml_str)
        parses given xml string
    add_action(action_type, action_args)
        adds the action of action_type with arguments given by the optional keyword
        argument action_args which is a list of lists where each element 
        is of the form [ArgumentName, ArgumentValue]
    write_model(model_name)
        write the model in BNGL format to the path given
    write_xml(open_file, xml_type)
        writes the XML of the model into the open_file object given. xml_types allowed
        are BNGXML or SBML formats.
    setup_simulator(sim_type)
        sets up a simulator in bngmodel.simulator where the only current supported 
        type of simulator is libRR for libRoadRunner simulator.
    '''
    def __init__(self, bngl_model, BNGPATH=def_bng_path):
        self.active_blocks = []
        # We want blocks to be printed in the same order
        # every time
        self._action_list = ["generate_network(", "generate_hybrid_model(","simulate(", "simulate_ode(", "simulate_ssa(", "simulate_pla(", "simulate_nf(", "parameter_scan(", "bifurcate(", "readFile(", "writeFile(", "writeModel(", "writeNetwork(", "writeXML(", "writeSBML(", "writeMfile(", "writeMexfile(", "writeMDL(", "visualize(", "setConcentration(", "addConcentration(", "saveConcentration(", "resetConcentrations(", "setParameter(", "saveParameters(", "resetParameters(", "quit(", "setModelName(", "substanceUnits(", "version(", "setOption("]
        self.block_order = ["parameters", "compartments", "moltypes", 
                            "species", "observables", "functions", 
                            "rules", "actions"]
        BNGPATH, bngexec = find_BNG_path(BNGPATH)
        self.BNGPATH = BNGPATH
        self.bngexec = bngexec 
        self.model_name = ""
        self.parse_model(bngl_model)

    @property
    def recompile(self):
        recompile = False
        for block in self.active_blocks:
            recompile = recompile or getattr(self, block)._recompile
        return recompile

    @property
    def changes(self):
        changes = {}
        for block in self.active_blocks:
            changes[block] = getattr(self, block)._changes
        return changes 

    def __str__(self):
        '''
        write the model to str
        '''
        model_str = "begin model\n"
        for block in self.block_order:
            if block in self.active_blocks:
                if block != "actions":
                    model_str += str(getattr(self, block))
        model_str += "\nend model\n"
        if "actions" in self.active_blocks:
            model_str += str(self.actions)
        return model_str

    def __repr__(self):
        return self.model_name

    def __iter__(self):
        active_ordered_blocks = [getattr(self,i) for i in self.block_order if i in self.active_blocks]
        return active_ordered_blocks.__iter__()

    def parse_model(self, model_file):
        # TODO We really need to clean up this method and relevant ones
        # and make it clear what each one of them does. Refactoring time! 
        
        # this route runs BNG2.pl on the bngl and parses
        # the XML instead
        if model_file.endswith(".bngl"):
            print("Attempting to generate XML")
            with TemporaryFile("w+") as xml_file:
                if self.generate_xml(model_file, xml_file):
                    print("Parsing XML")
                    # import IPython;IPython.embed()
                    self.parse_xml(xml_file.read())
                    self.reset_compilation_tags()
                else:
                    print("XML file couldn't be generated")
        elif model_file.endswith(".xml"):
            with open(model_file, "r") as f:
                xml_str = f.read()
                self.parse_xml(xml_str)
            self.reset_compilation_tags()
        else:
            print("The extension of {} is not supported".format(model_file))
            raise NotImplemented

    def reset_compilation_tags(self):
        for block in self.active_blocks:
            getattr(self, block).reset_compilation_tags()

    def generate_xml(self, model_file, xml_file):
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

    def strip_actions(self, model_path, folder):
        '''
        Strips actions from a BNGL folder and makes a copy
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

    def _not_action(self, line):
        for action in self._action_list:
            if action in line:
                return False
        return True

    def parse_xml(self, xml_str):
        xml_dict = xmltodict.parse(xml_str)
        self.xml_dict = xml_dict
        xml_model = xml_dict['sbml']['model']
        self.model_name = xml_model['@id']
        for listkey in xml_model.keys():
            if listkey == "ListOfParameters":
                param_list = xml_model[listkey]
                if param_list is not None:
                    params = param_list['Parameter']
                    self.parameters = Parameters()
                    self.parameters.parse_xml_block(params)
                    self.active_blocks.append("parameters")
            elif listkey == "ListOfObservables":
                obs_list = xml_model[listkey]
                if obs_list is not None:
                    obs = obs_list['Observable']
                    self.observables = Observables()
                    self.observables.parse_xml_block(obs)
                    self.active_blocks.append("observables")
            elif listkey == "ListOfCompartments":
                comp_list = xml_model[listkey]
                if comp_list is not None:
                    self.compartments = Compartments()
                    comps = comp_list['compartment']
                    self.compartments.parse_xml_block(comps)
                    self.active_blocks.append("compartments")
            elif listkey == "ListOfMoleculeTypes":
                mtypes_list = xml_model[listkey]
                if mtypes_list is not None:
                    mtypes = mtypes_list["MoleculeType"]
                    self.moltypes = MoleculeTypes()
                    self.moltypes.parse_xml_block(mtypes)
                    self.active_blocks.append("moltypes")
            elif listkey == "ListOfSpecies":
                species_list = xml_model[listkey]
                if species_list is not None:
                    species = species_list["Species"]
                    self.species = Species()
                    self.species.parse_xml_block(species)
                    self.active_blocks.append("species")
            elif listkey == "ListOfReactionRules":
                rrules_list = xml_model[listkey]
                if rrules_list is not None:
                    rrules = rrules_list["ReactionRule"]
                    self.rules = Rules()
                    self.rules.parse_xml_block(rrules)
                    self.active_blocks.append("rules")
            elif listkey == "ListOfFunctions":
                # TODO: Optional expression parsing?
                # TODO: Add arguments correctly
                func_list = xml_model[listkey]
                if func_list is not None:
                    self.functions = Functions()
                    funcs = func_list['Function']
                    self.functions.parse_xml_block(funcs)
                    self.active_blocks.append("functions")
        # And that's the end of parsing
        print("XML parsed")

    def add_action(self, action_type, action_args=[]):
        # add actions block and to active list
        if not hasattr(self, "actions"):
            self.actions = Actions()
            self.active_blocks.append("actions")
        self.actions.add_action(action_type, action_args)

    def write_model(self, file_name):
        '''
        write the model to file 
        '''
        model_str = ""
        for block in self.active_blocks:
            model_str += str(getattr(self, block))
        with open(file_name, 'w') as f:
            f.write(model_str)

    def write_xml(self, open_file, xml_type="bngxml"):
        '''
        write new XML to file by calling BNG2.pl again
        '''
        cur_dir = os.getcwd()
        # temporary folder to work in
        with TemporaryDirectory() as temp_folder:
            # write the current model to temp folder
            os.chdir(temp_folder)
            with open("temp.bngl", "w") as f:
                f.write(str(self))
            # run with --xml 
            # TODO: Make output supression an option somewhere
            if xml_type == "bngxml":
                rc = subprocess.run(["perl",self.bngexec, "--xml", "temp.bngl"], stdout=bng.defaults.stdout)
                if rc.returncode == 1:
                    print("XML generation failed")
                    # go back to our original location
                    os.chdir(cur_dir)
                    return False
                else:
                    # we should now have the XML file 
                    with open("temp.xml", "r") as f:
                        content = f.read()
                        open_file.write(content)
                    # go back to beginning
                    open_file.seek(0)
                    os.chdir(cur_dir)
                    return True
            elif xml_type == "sbml":
                rc = subprocess.run(["perl",self.bngexec, "temp.bngl"], stdout=bng.defaults.stdout)
                if rc.returncode == 1:
                    print("SBML generation failed")
                    # go back to our original location
                    os.chdir(cur_dir)
                    return False
                else:
                    # we should now have the SBML file 
                    with open("temp_sbml.xml", "r") as f:
                        content = f.read()
                        open_file.write(content)
                    open_file.seek(0)
                    os.chdir(cur_dir)
                    return True
            else: 
                print("XML type {} not recognized".format(xml_type))
            return False

    def setup_simulator(self, sim_type="libRR"):
        '''
        Sets up a simulator attribute that is a generic front-end
        to all other simulators. At the moment only libroadrunner
        is supported
        '''
        if sim_type == "libRR":
            # we need to add writeSBML action for now
            self.add_action("generate_network", [("overwrite",1)])
            self.add_action("writeSBML", [])
            # temporary file
            with TemporaryFile(mode="w+") as tpath:
                # write the sbml
                self.write_xml(tpath, xml_type="sbml")
                # TODO: Only clear the writeSBML action
                # by adding a mechanism to do so
                self.actions.clear_actions()
                # get the simulator
                self.simulator = bng.sim_getter(model_str=tpath.read(), sim_type=sim_type)
        else:
            print("Sim type {} is not recognized, only libroadrunner \
                   is supported currently by passing libRR to \
                   sim_type keyword argument".format(sim_type))
        return self.simulator

###### CORE OBJECT AND PARSING FRONT-END ######

if __name__ == "__main__":
    # this is to run through a set of 
    # bngl files under the folder validation
    os.chdir("validation")
    bngl_list = os.listdir(os.getcwd())
    bngl_list = filter(lambda x: x.endswith(".bngl"), bngl_list)
    for bngl in bngl_list:
        m = bngmodel(bngl)
        with open('test.bngl', 'w') as f:
            f.write(str(m))
        rc = subprocess.run([m.bngexec, 'test.bngl'])
        if rc.returncode == 1:
            print("issues with the written bngl")
            sys.exit()
