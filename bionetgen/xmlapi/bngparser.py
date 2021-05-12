import xmltodict

from bionetgen.main import BioNetGen
from tempfile import TemporaryFile

from .bngfile import BNGFile
from .structs import Parameters, Species, MoleculeTypes, Observables, Functions, Compartments, Rules, Actions

# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config['bionetgen']
def_bng_path = conf['bngpath']

class BNGParser:
    '''
    Parser object that deals with reading in the BNGL file and 
    setting up the model object

    Usage: BNGParser(bngl_path)
           BNGParser(bngl_path, BNGPATH)

    Attributes
    ----------
    bngfile : BNGFile
        BNGFile object that's responsible for .bngl file manipulations
    
    Methods
    -------
    parse_model(model_file)
        parses the BNGL model at the given path and adds everything to a given model object
    parse_xml(xml_str)
        parses given xml string and adds everything to a given model object
    '''
    def __init__(self, path, BNGPATH=def_bng_path) -> None:
        self.bngfile = BNGFile(path)
    
    def parse_model(self, model_obj) -> None:
        '''
        Will determine the parser route eventually and call the right
        parser 
        '''
        self._parse_model_bngpl(model_obj)

    def _parse_model_bngpl(self, model_obj) -> None:      
        # get file path
        model_file = self.bngfile.path
        
        # this route runs BNG2.pl on the bngl and parses
        # the XML instead
        if model_file.endswith(".bngl"):
            print("Attempting to generate XML")
            with TemporaryFile("w+") as xml_file:
                if self.bngfile.generate_xml(xml_file):
                    print("Parsing XML")
                    self.parse_xml(xml_file.read(), model_obj)
                    model_obj.reset_compilation_tags()
                else:
                    print("XML file couldn't be generated")
        elif model_file.endswith(".xml"):
            with open(model_file, "r") as f:
                xml_str = f.read()
                self.parse_xml(xml_str, model_obj)
            model_obj.reset_compilation_tags()
        else:
            print("The extension of {} is not supported".format(model_file))
            raise NotImplemented

    def parse_xml(self, xml_str, model_obj) -> None:
        xml_dict = xmltodict.parse(xml_str)
        model_obj.xml_dict = xml_dict
        xml_model = xml_dict['sbml']['model']
        model_obj.model_name = xml_model['@id']
        for listkey in xml_model.keys():
            if listkey == "ListOfParameters":
                param_list = xml_model[listkey]
                if param_list is not None:
                    params = param_list['Parameter']
                    model_obj.parameters = Parameters()
                    model_obj.parameters.parse_xml_block(params)
                    model_obj.active_blocks.append("parameters")
            elif listkey == "ListOfObservables":
                obs_list = xml_model[listkey]
                if obs_list is not None:
                    obs = obs_list['Observable']
                    model_obj.observables = Observables()
                    model_obj.observables.parse_xml_block(obs)
                    model_obj.active_blocks.append("observables")
            elif listkey == "ListOfCompartments":
                comp_list = xml_model[listkey]
                if comp_list is not None:
                    model_obj.compartments = Compartments()
                    comps = comp_list['compartment']
                    model_obj.compartments.parse_xml_block(comps)
                    model_obj.active_blocks.append("compartments")
            elif listkey == "ListOfMoleculeTypes":
                mtypes_list = xml_model[listkey]
                if mtypes_list is not None:
                    mtypes = mtypes_list["MoleculeType"]
                    model_obj.moltypes = MoleculeTypes()
                    model_obj.moltypes.parse_xml_block(mtypes)
                    model_obj.active_blocks.append("moltypes")
            elif listkey == "ListOfSpecies":
                species_list = xml_model[listkey]
                if species_list is not None:
                    species = species_list["Species"]
                    model_obj.species = Species()
                    model_obj.species.parse_xml_block(species)
                    model_obj.active_blocks.append("species")
            elif listkey == "ListOfReactionRules":
                rrules_list = xml_model[listkey]
                if rrules_list is not None:
                    rrules = rrules_list["ReactionRule"]
                    model_obj.rules = Rules()
                    model_obj.rules.parse_xml_block(rrules)
                    model_obj.active_blocks.append("rules")
            elif listkey == "ListOfFunctions":
                # TODO: Optional expression parsing?
                # TODO: Add arguments correctly
                func_list = xml_model[listkey]
                if func_list is not None:
                    model_obj.functions = Functions()
                    funcs = func_list['Function']
                    model_obj.functions.parse_xml_block(funcs)
                    model_obj.active_blocks.append("functions")
        # And that's the end of parsing
        print("XML parsed")