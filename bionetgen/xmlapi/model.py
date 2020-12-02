import bionetgen as bng
import re, functools, subprocess, os, xmltodict, sys, shutil, tempfile
from .utils import find_BNG_path
from .structs import Parameters, Species, MoleculeTypes, Observables, Functions, Compartments, Rules, Actions

def_bng_path = bng.defaults.bng_path

###### CORE OBJECT AND PARSING FRONT-END ######
class bngmodel:
    '''
    The full model
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
        # this route runs BNG2.pl on the bngl and parses
        # the XML instead
        if model_file.endswith(".bngl"):
            # TODO: Strip actions into a temp file
            # then run the gen xml 
            print("Attempting to generate XML")
            model_file, tfolder = self.generate_xml(model_file)
            if model_file is not None:
                print("Parsing XML")
                self.parse_xml(model_file)
                self.reset_compilation_tags()
            else:
                print("XML file doesn't exist")
            shutil.rmtree(tfolder)
        elif model_file.endswith(".xml"):
            self.parse_xml(model_file)
            self.reset_compilation_tags()
        else:
            print("The extension of {} is not supported".format(model_file))
            raise NotImplemented

    def reset_compilation_tags(self):
        for block in self.active_blocks:
            getattr(self, block).reset_compilation_tags()

    def generate_xml(self, model_file):
        cur_dir = os.getcwd()
        # temporary folder to work in
        temp_folder = tempfile.mkdtemp()
        # make a stripped copy without actions in the folder
        stripped_bngl = self.strip_actions(model_file, temp_folder)
        # run with --xml 
        os.chdir(temp_folder)
        # TODO: Make output supression an option somewhere
        rc = subprocess.run(["perl",self.bngexec, "--xml", stripped_bngl], stdout=bng.defaults.stdout)
        if rc.returncode == 1:
            print("XML generation failed")
            # go back to our original location
            os.chdir(cur_dir)
            shutil.rmtree(temp_folder)
            return None
        else:
            # we should now have the XML file 
            path, model_name = os.path.split(stripped_bngl)
            model_name = model_name.replace(".bngl", "")
            xml_file = model_name + ".xml"
            # go back to our original location
            os.chdir(cur_dir)
            return os.path.join(path, xml_file), path

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

    def parse_xml(self, model_file):
        with open(model_file, "r") as f:
            xml_str = "".join(f.readlines())
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

    def write_xml(self, file_name, xml_type="bngxml"):
        '''
        write new XML to file by calling BNG2.pl again
        '''
        cur_dir = os.getcwd()
        # temporary folder to work in
        temp_folder = tempfile.mkdtemp()
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
            else:
                # we should now have the XML file 
                fpath = os.path.join(cur_dir, file_name)
                shutil.copy("temp.xml", fpath)
                os.chdir(cur_dir)
        elif xml_type == "sbml":
            rc = subprocess.run(["perl",self.bngexec, "temp.bngl"], stdout=bng.defaults.stdout)
            if rc.returncode == 1:
                print("SBML generation failed")
                # go back to our original location
                os.chdir(cur_dir)
            else:
                # we should now have the SBML file 
                fpath = os.path.join(cur_dir, file_name)
                shutil.copy("temp_sbml.xml", fpath)
                os.chdir(cur_dir)
        else: 
            print("XML type {} not recognized".format(xml_type))
        # we need to remove the temporary folder
        shutil.rmtree(temp_folder)

    def setup_simulator(self, sim_type="libRR"):
        # we need to add writeSBML action for now
        self.add_action("generate_network", [("overwrite",1)])
        self.add_action("writeSBML", [])
        # temporary file
        tfile, tpath = tempfile.mkstemp()
        # write the sbml 
        self.write_xml(tpath, xml_type="sbml")
        # TODO: Only clear the writeSBML action
        # by adding a mechanism to do so
        self.actions.clear_actions()
        # get the simulator
        self.simulator = bng.sim_getter(tpath, sim_type)
        os.remove(tpath)
        return self.simulator

###### CORE OBJECT AND PARSING FRONT-END ######

if __name__ == "__main__":
    # this is to run through a set of 
    # bngl files under the folder validation
    os.chdir("validation")
    bngl_list = os.listdir(os.getcwd())
    bngl_list = filter(lambda x: x.endswith(".bngl"), bngl_list)
    for bngl in bngl_list:
        m = BNGModel(bngl)
        with open('test.bngl', 'w') as f:
            f.write(str(m))
        rc = subprocess.run([m.bngexec, 'test.bngl'])
        if rc.returncode == 1:
            print("issues with the written bngl")
            sys.exit()
