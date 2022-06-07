import xmltodict, re

from bionetgen.main import BioNetGen
from bionetgen.core.exc import BNGParseError, BNGModelError
from tempfile import TemporaryFile

from .bngfile import BNGFile
from .xmlparsers import ParameterBlockXML, CompartmentBlockXML, ObservableBlockXML
from .xmlparsers import SpeciesBlockXML, MoleculeTypeBlockXML, FunctionBlockXML
from .xmlparsers import RuleBlockXML, EnergyPatternBlockXML, PopulationMapBlockXML
from .blocks import ActionBlock
from bionetgen.core.utils.utils import ActionList

# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config["bionetgen"]
def_bng_path = conf["bngpath"]


class BNGParser:
    """
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
    """

    def __init__(
        self, path, BNGPATH=def_bng_path, parse_actions=True, generate_network=False
    ) -> None:
        self.to_parse_actions = parse_actions
        self.bngfile = BNGFile(path, generate_network=generate_network)
        self.alist = ActionList()
        self.alist.define_parser()

    def parse_model(self, model_obj) -> None:
        """
        Will determine the parser route eventually and call the right
        parser
        """
        self._parse_model_bngpl(model_obj)
        if self.to_parse_actions:
            self.parse_actions(model_obj)

    def _parse_model_bngpl(self, model_obj) -> None:
        # get file path
        model_file = self.bngfile.path

        # this route runs BNG2.pl on the bngl and parses
        # the XML instead
        if model_file.endswith(".bngl"):
            # TODO: Add verbosity option to the library
            # print("Attempting to generate XML")
            with TemporaryFile("w+") as xml_file:
                if self.bngfile.generate_xml(xml_file):
                    # TODO: Add verbosity option to the library
                    xmlstr = xml_file.read()
                    # < is not a valid XML character, we need to replace it
                    xmlstr = xmlstr.replace('relation="<', 'relation="&lt;')
                    self.parse_xml(xmlstr, model_obj)
                    model_obj.reset_compilation_tags()
                else:
                    raise BNGModelError(
                        self.bngfile.path, message="XML file couldn't be generated"
                    )
        elif model_file.endswith(".xml"):
            with open(model_file, "r") as f:
                xml_str = f.read()
                # < is not a valid XML character, we need to replace it
                xmlstr = xml_str.replace('relation="<', 'relation="&lt;')
                self.parse_xml(xml_str, model_obj)
            model_obj.reset_compilation_tags()
        else:
            raise NotImplementedError(
                "The extension of {} is not supported".format(model_file)
            )

    def parse_actions(self, model_obj):
        if len(self.bngfile.parsed_actions) > 0:
            ablock = ActionBlock()
            # we have actions in file, let's get them
            # import ipdb;ipdb.set_trace()
            left = []
            for action in self.bngfile.parsed_actions:
                # some cleanup, first we remove comments
                action = re.sub(r"\#.*", "", action)
                # now we remove whitespaces
                action = re.sub(r"\s", "", action)
                # if we don't have anything left, move on
                if len(action) == 0:
                    continue
                # use pyparsing for parsing the action into a list
                try:
                    action_list = self.alist.action_parser.parseString(action)
                except Exception as e:
                    raise BNGParseError(
                        self.bngfile.path, f"Failed to parse action {action}"
                    )
                # we could have ";" in the action, so we need to remove it
                if action_list[-1] == ";":
                    _ = action_list.pop(-1)
                # we we move onto actually making the action object
                # first value is always the action type, remove
                atype = action_list.pop(0)
                # all actions have "()", remove
                action_list = action_list[1:-1]
                # be done if we don't have anything left
                if len(action_list) == 0:
                    # we don't have any arguments
                    ablock.add_action(atype, {})
                    continue
                # we have arguments now onto argument parsing
                # we check the action type and process accordingly
                if atype in self.alist.no_setter_syntax:
                    # these are actions like setParameter("test", 10), setModelName("name")
                    if len(action_list) == 1:
                        # this is of the form action("argument")
                        ablock.add_action(atype, {action_list[0]: None})
                        continue
                    elif len(action_list) == 3:
                        # TODO: Error checking here!
                        if action_list[1] == ",":
                            # this is of the form action(argument, value)
                            ablock.add_action(
                                atype, {action_list[0]: None, action_list[2]: None}
                            )
                            continue
                elif atype in self.alist.square_braces:
                    # these are actions like saveParameters(["a","b"])
                    # TODO: Error checking here!
                    if action_list[0] == "[":
                        # remove square braces
                        action_list = action_list[1:-1]
                    arg_dict = {}
                    for arg in action_list:
                        arg_dict[arg] = None
                    ablock.add_action(atype, arg_dict)
                    continue
                elif atype in self.alist.normal_types:
                    # finally a normal action, we have {} and => syntax
                    # TODO: Error checking here!
                    if action_list[0] == "{":
                        # remove curly braces
                        action_list = action_list[1:-1]
                    arg_dict = {}
                    if len(action_list) == 0:
                        ablock.add_action(atype, arg_dict)
                        continue
                    while len(action_list) > 0:
                        arg_name = action_list.pop(0)
                        connector = action_list.pop(0)
                        if connector != "=>":
                            raise BNGParseError(
                                self.bngfile.path, f"Action {action} is malformed"
                            )
                        if arg_name in self.alist.irregular_args:
                            arg_type = self.alist.irregular_args[arg_name]
                            if arg_type == "dict":
                                # process dict
                                start_curly = action_list.pop(0)
                                # make sure we are actually reading a dict
                                if start_curly != "{":
                                    raise BNGParseError(
                                        self.bngfile.path,
                                        f"Action {action} is malformed",
                                    )
                                value_str = "{"
                                end_curly = None
                                while end_curly is None:
                                    # we are looping over A, =>, B and want to
                                    # generate { A=>B, C=>D, etc }
                                    dict_key = action_list.pop(0)
                                    if dict_key == "}":
                                        # we are done
                                        end_curly = dict_key
                                    else:
                                        if len(value_str) > 1:
                                            value_str += ","
                                        dict_conn = action_list.pop(0)
                                        dict_val = action_list.pop(0)
                                        if dict_conn != "=>":
                                            raise BNGParseError(
                                                self.bngfile.path,
                                                f"Action {action} is malformed",
                                            )
                                        value_str += dict_key + dict_conn + dict_val
                                value_str += "}"
                                arg_value = value_str
                            elif arg_type == "list":
                                # process list
                                start_curly = action_list.pop(0)
                                # make sure we are actually reading a dict
                                if start_curly != "[":
                                    raise BNGParseError(
                                        self.bngfile.path,
                                        f"Action {action} is malformed",
                                    )
                                value_str = "["
                                end_curly = None
                                while end_curly is None:
                                    argument_element = action_list.pop(0)
                                    if argument_element == "]":
                                        end_curly = argument_element
                                    else:
                                        if len(value_str) > 1:
                                            value_str += ","
                                        value_str += argument_element
                                value_str += "]"
                                arg_value = value_str
                        else:
                            arg_value = action_list.pop(0)
                        arg_dict[arg_name] = arg_value
                    ablock.add_action(atype, arg_dict)
                    continue
                else:
                    raise BNGParseError(
                        self.bngfile.path, f"Action type {atype} is not recognized."
                    )
            model_obj.add_block(ablock)

    def parse_xml(self, xml_str, model_obj) -> None:
        xml_dict = xmltodict.parse(xml_str)
        # catch non-BNG XML files
        if "sbml" not in xml_dict:
            if "model" not in xml_dict["sbml"]:
                raise BNGParseError(
                    self.bngfile.path,
                    "Input model is invalid. Please ensure model is in proper BNGL or BNG-XML format",
                )
        model_obj.xml_dict = xml_dict
        first_key = list(xml_dict.keys())[0]
        xml_model = xml_dict[first_key]["model"]
        model_obj.model_name = xml_model["@id"]
        for listkey in xml_model.keys():
            if listkey == "ListOfParameters":
                param_list = xml_model[listkey]
                if param_list is not None:
                    params = param_list["Parameter"]
                    xml_parser = ParameterBlockXML(params)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfObservables":
                obs_list = xml_model[listkey]
                if obs_list is not None:
                    obs = obs_list["Observable"]
                    xml_parser = ObservableBlockXML(obs)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfCompartments":
                comp_list = xml_model[listkey]
                if comp_list is not None:
                    comps = comp_list["compartment"]
                    xml_parser = CompartmentBlockXML(comps)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfMoleculeTypes":
                mtypes_list = xml_model[listkey]
                if mtypes_list is not None:
                    mtypes = mtypes_list["MoleculeType"]
                    xml_parser = MoleculeTypeBlockXML(mtypes)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfSpecies":
                species_list = xml_model[listkey]
                if species_list is not None:
                    species = species_list["Species"]
                    xml_parser = SpeciesBlockXML(species)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfReactionRules":
                rrules_list = xml_model[listkey]
                if rrules_list is not None:
                    rrules = rrules_list["ReactionRule"]
                    xml_parser = RuleBlockXML(rrules)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfFunctions":
                # TODO: Optional expression parsing?
                # TODO: Add arguments correctly
                func_list = xml_model[listkey]
                if func_list is not None:
                    funcs = func_list["Function"]
                    xml_parser = FunctionBlockXML(funcs)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfEnergyPatterns":
                ep_list = xml_model[listkey]
                if ep_list is not None:
                    eps = ep_list["EnergyPattern"]
                    xml_parser = EnergyPatternBlockXML(eps)
                    model_obj.add_block(xml_parser.parsed_obj)
            elif listkey == "ListOfPopulationMaps":
                pm_list = xml_model[listkey]
                if pm_list is not None:
                    pms = pm_list["PopulationMap"]
                    xml_parser = PopulationMapBlockXML(pms)
                    model_obj.add_block(xml_parser.parsed_obj)
        # And that's the end of parsing
        # TODO: Add verbosity option to the library
        # print("Parsing complete")
