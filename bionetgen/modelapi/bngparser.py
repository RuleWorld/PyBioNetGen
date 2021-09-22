import xmltodict, re

from bionetgen.main import BioNetGen
from tempfile import TemporaryFile

from .bngfile import BNGFile
from .xmlparsers import ParameterBlockXML, CompartmentBlockXML, ObservableBlockXML
from .xmlparsers import SpeciesBlockXML, MoleculeTypeBlockXML, FunctionBlockXML
from .xmlparsers import RuleBlockXML
from .blocks import ActionBlock

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

    def __init__(self, path, BNGPATH=def_bng_path, parse_actions=True) -> None:
        self.to_parse_actions = parse_actions
        self.bngfile = BNGFile(path)

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
                    raise ValueError("XML file couldn't be generated")
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
            # import ipdb;ipdb.set_trace();
            ablock = ActionBlock()
            # we have actions in file, let's get them
            for action in self.bngfile.parsed_actions:
                action = re.sub(
                    r"\#.*", "", action
                )  # should this be (r"\#.*) or just ("\#.*")
                action = re.sub(
                    r"\s", "", action
                )  # should this be (r"\s) or just ("\s")
                if len(action) == 0:
                    continue
                m = re.match(r"^\s*(\S+)\(\s*(\S*)\s*\)(\;)?\s*(\#\s*\S*)?\s*", action)
                if m is not None:
                    # here we have an action
                    atype = m.group(1)
                    in_parens = m.group(2)
                    if len(in_parens) > 0:
                        # in parenthesis group can have curly or square braces
                        m = re.match(r"\{(\S*)\}$", in_parens)
                        arg_dict = {}
                        if m is not None:
                            arg_list_str = m.group(1)
                            # First let's check for lists
                            # Please note that this will only replace a single list that doesn't reoccur
                            L = re.match(r"\S+\[(\S*)\]\S*", m.group(1))
                            if L is not None:
                                arg_list_str = arg_list_str.replace(
                                    f"[{L.group(1)}]",
                                    f"[{L.group(1).replace(',','_')}]",
                                )
                            # Now check for curly braces
                            # Please note that this will only replace a single dictionary that doesn't reoccur
                            L = re.match(r"\S+\{(\S*)\}\S*", m.group(1))
                            if L is not None:
                                arg_list_str = arg_list_str.replace(
                                    "{%s}" % L.group(1),
                                    "{%s}" % L.group(1).replace(",", "_"),
                                )
                            arg_list = arg_list_str.split(",")
                            for arg_str in arg_list:
                                splt = arg_str.split("=>")
                                if len(splt) > 1:
                                    arg = splt[0]
                                    val = "=>".join(splt[1:])
                                    # now we need to check if we have a list/dictionary
                                    if "_" in val:
                                        val = val.replace("_", ",")
                                    # add the tuple to the list
                                    if arg in arg_dict:
                                        # TODO: make this a warning
                                        print(
                                            f"WARNING: argument {arg} for action {atype} is given twice, using the last value {val}"
                                        )
                                    arg_dict[arg] = val
                        else:
                            m = re.match(r"\[(\S*)\]", in_parens)
                            if m is not None:
                                # this is a list of items
                                arg_list_str = m.group(1)
                            else:
                                # what we have in parentheses has to
                                # be a simple list of arguments
                                arg_list_str = in_parens
                            arg_list = arg_list_str.split(",")
                            for arg_str in arg_list:
                                # add to arg_tuples
                                if arg_str in arg_dict:
                                    # TODO: make this a warning
                                    print(
                                        f"WARNING: argument {arg_str} for action {atype} is given twice"
                                    )
                                arg_dict[arg_str] = None
                        ablock.add_action(atype, arg_dict)
                    else:
                        ablock.add_action(atype, {})
            model_obj.add_block(ablock)

    def parse_xml(self, xml_str, model_obj) -> None:
        xml_dict = xmltodict.parse(xml_str)
        model_obj.xml_dict = xml_dict
        xml_model = xml_dict["sbml"]["model"]
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
        # And that's the end of parsing
        # TODO: Add verbosity option to the library
        # print("Parsing complete")
