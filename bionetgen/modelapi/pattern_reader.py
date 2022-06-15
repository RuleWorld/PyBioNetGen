from bionetgen.core.utils.logging import BNGLogger
from bionetgen.modelapi.pattern import Pattern, Molecule, Component
import pyparsing as pp


class BNGParsers:
    """
    Container for parsers for the reader
    """

    def __init__(self) -> None:
        pass


class BNGPatternReader:
    """
    Class that generates parsers to read BNG pattern strings and
    form Pattern objects from them.

    Usage: BNGPatternReader(pattern_string)

    Arguments
    ---------
    pattern_str : str
        The pattern string to read and generate a Pattern object from

    Attributes
    ----------
    pattern : Pattern
        The Pattern object formed from the parsed string
    parsers : BNGParsers
        Container object that has parsers for various parts of a
        BNG pattern string

    Methods
    -------
    define_parsers : None
        runs other defined parser commands to setup all parsers
    define_component_parser : None
        defines pyparsing parser for components
    define_molecule_parser : None
        defines pyparsing parser for molecules
    define_pattern_parser : None
        defines pyparsing parser for overall patterns
    make_pattern : Pattern
        forms the actual Pattern object from the pattern string
        using the defined parsers
    """

    def __init__(self, pattern_str) -> None:
        self.logger = BNGLogger()
        self.pattern_str = pattern_str
        self.parsers = BNGParsers()
        self.define_parsers()
        self.pattern = self.make_pattern(self.pattern_str)

    def define_parsers(self):
        self.define_component_parser()
        self.define_molecule_parser()
        self.define_pattern_parser()

    def define_component_parser(self):
        """
        Defines specific parsers for BNG components
        """
        # bng names are alpha numericals and _1
        self.parsers.base_name = pp.Word(pp.alphas, pp.alphanums + "_")
        # components have optional states and bonds
        self.parsers.state = pp.Combine(
            pp.Word("~") + (self.parsers.base_name ^ pp.Word(pp.nums))
        ) ^ pp.Word("~?")
        self.parsers.bond = pp.Combine(
            (pp.Word("!") + pp.Word(pp.nums)) ^ (pp.Word("!?")) ^ (pp.Word("!+"))
        )
        self.parsers.component = (
            self.parsers.base_name
            + pp.Optional(self.parsers.state)
            + pp.Optional(self.parsers.bond)
        )
        component_parser = pp.Combine(self.parsers.component)
        # components are separated by commas
        component_separator = pp.Word(",")
        self.parsers.components_parser = pp.delimited_list(
            component_parser, delim=component_separator
        )
        self.parsers.combined_components_parser = pp.delimited_list(
            component_parser, delim=component_separator, combine=True
        )

    def define_molecule_parser(self):
        """
        Defines specific parsers for BNG molecules
        """
        # molecules can have tags
        self.parsers.tag = pp.Combine(
            pp.Word("%") + (self.parsers.base_name ^ pp.Word(pp.nums))
        )
        # and compartments
        self.parsers.compartment = pp.Combine(pp.Word("@") + self.parsers.base_name)
        # combine tag and compartment
        tag_comp = (
            pp.Optional(self.parsers.tag) + pp.Optional(self.parsers.compartment)
        ) ^ (pp.Optional(self.parsers.compartment) + pp.Optional(self.parsers.tag))
        # full molecule
        self.parsers.molecule = (
            self.parsers.base_name
            + tag_comp
            + pp.Word("(")
            + pp.Optional(self.parsers.combined_components_parser)
            + pp.Word(")")
            + tag_comp
        )
        molecule_parser = pp.Combine(self.parsers.molecule)
        # molecules
        # components are separated by commas
        molecule_separator = pp.Word(".")
        self.parsers.molecules_parser = pp.delimited_list(
            molecule_parser, delim=molecule_separator
        )
        self.parsers.combined_molecules_parser = pp.delimited_list(
            molecule_parser, delim=molecule_separator, combine=True
        )

    def define_pattern_parser(self):
        """
        Defines specific parsers for overall BNG patterns
        """
        # a pattern can start with a tag or a compartment
        mods = pp.Word("$") ^ pp.Word("{MatchOnce}")
        # zero molecule is a simple 0
        zeroMolecule = pp.Word("0")
        # quantifier
        quantifier = pp.Combine(
            (
                pp.Word("<")
                ^ pp.Word("<=")
                ^ pp.Word("==")
                ^ pp.Word(">=")
                ^ pp.Word(">")
            )
            + pp.Word(pp.nums)
        )
        # combine tag and compartment
        tag = self.parsers.tag + (pp.Word(":") ^ pp.Word("::"))
        comp = self.parsers.compartment + (pp.Word(":") ^ pp.Word("::"))
        tag_comp_1 = (
            self.parsers.tag + self.parsers.compartment + (pp.Word(":") ^ pp.Word("::"))
        )
        tag_comp_2 = (
            self.parsers.compartment + self.parsers.tag + (pp.Word(":") ^ pp.Word("::"))
        )
        tag_comp = tag ^ comp ^ tag_comp_1 ^ tag_comp_2
        pattern = (
            pp.Optional(tag_comp)
            + pp.Optional(mods)
            + self.parsers.combined_molecules_parser
            + pp.Optional(quantifier)
        )
        # full pattern
        self.parsers.pattern = pattern ^ zeroMolecule

    def make_pattern(self, pattern_str):
        """
        Forms the Pattern object from the given string using the
        parsed defined above.
        """
        # if pattern_str == "X()":
        #     # import ipdb;ipdb.set_trace()
        #     import IPython,sys;IPython.embed();sys.exit()
        # set location for logging
        log_loc = f"{__file__} : BNGPatternReader.make_pattern()"
        # instantiate a pattern
        pattern = Pattern(molecules=[])
        # start parsing
        parsed_pattern = self.parsers.pattern.parseString(pattern_str)
        split_molecs = None
        # first we'll pull out any features that are pattern only
        for parsed_val in parsed_pattern:
            # these are pattern features and the entire molecules section
            if parsed_val.startswith("@"):
                # this is a pattern-wide compartment
                self.logger.debug(f"found compartment in {parsed_val}", loc=log_loc)
                pattern.compartment = parsed_val.replace("@", "")
                continue
            elif parsed_val.startswith("%"):
                # this is a pattern-wide tag
                self.logger.debug(f"found tag in {parsed_val}", loc=log_loc)
                pattern.label = parsed_val.replace("%", "")
                continue
            elif parsed_val.startswith(":"):
                # this is a pattern-wide separator
                self.logger.debug(f"found separator in {parsed_val}", loc=log_loc)
                continue
            elif ("$" in parsed_val) or ("{MatchOnce}" in parsed_val):
                # this is a constant value species pattern or a MatchOnce observable
                self.logger.debug(f"found mod in {parsed_val}", loc=log_loc)
                if "$" in parsed_val:
                    pattern.fixed = True
                elif "{MatchOnce}" in parsed_val:
                    pattern.MatchOnce = True
                continue
            elif (
                ("<" in parsed_val)
                or ("<=" in parsed_val)
                or ("==" in parsed_val)
                or (">=" in parsed_val)
                or (">" in parsed_val)
            ):
                self.logger.debug(f"found quantifier in {parsed_val}", loc=log_loc)
                if "==" in parsed_val:
                    pattern.relation = "=="
                elif "<=" in parsed_val:
                    pattern.relation = "<="
                elif ">=" in parsed_val:
                    pattern.relation = ">="
                elif "<" in parsed_val:
                    pattern.relation = "<"
                elif ">" in parsed_val:
                    pattern.relation = ">"
                pattern.quantity = int(parsed_val.replace(pattern.relation, ""))
                # this is a quantifier
                continue
            elif parsed_val == "0":
                # this is a zero molecule
                m = Molecule(components=[])
                m.parent_pattern = pattern
                pattern.molecules.append(m)
                self.logger.debug(f"found zero molecule in {parsed_val}", loc=log_loc)
                continue
            # only molecules should be remaining
            split_molecs = self.parsers.molecules_parser.parseString(parsed_val)
        # if we had a zero molecule we are done
        if split_molecs is None:
            # this is the zero molecule
            self.logger.debug(
                f"no molecules found in: {self.pattern_str}, done", loc=log_loc
            )
            return pattern
        # we got the molecule list, let's loop over molecules now
        self.logger.debug(f"molecules: {split_molecs}", loc=log_loc)
        for molec_str in split_molecs:
            molecule = Molecule(components=[])
            molecule.parent = pattern
            # each molec str is a molecule string with all features
            parsed_molec = self.parsers.molecule.parseString(molec_str)
            self.logger.debug(f"parsed molecule: {parsed_molec}", loc=log_loc)
            in_molec = False
            for parsed_val in parsed_molec:
                # we need to pull out the molecule features
                if parsed_val.startswith("@"):
                    # this is a molecule compartment
                    self.logger.debug(f"found compartment in {parsed_val}", loc=log_loc)
                    molecule.compartment = parsed_val.replace("@", "")
                    continue
                elif parsed_val.startswith("%"):
                    # this is a molecule tag
                    self.logger.debug(f"found tag in {parsed_val}", loc=log_loc)
                    molecule.label = parsed_val.replace("%", "")
                    continue
                elif parsed_val == "(" or parsed_val == ")":
                    if parsed_val == "(":
                        in_molec = True
                    else:
                        in_molec = False
                    # this molecule opening and closing
                    self.logger.debug(f"found paran in {parsed_val}", loc=log_loc)
                    continue
                if not in_molec:
                    # if we aren't in molecule yet, this can only be the name
                    molecule.name = parsed_val
                else:
                    # only components remain, parse those and loop
                    split_components = self.parsers.components_parser.parseString(
                        parsed_val
                    )
                    self.logger.debug(
                        f"split components: {split_components}", loc=log_loc
                    )
                    for component_str in split_components:
                        # each component is parsed separately now
                        parsed_component = self.parsers.component.parseString(
                            component_str
                        )

                        component = Component()
                        component.parent_molecule = molecule
                        # import ipdb;ipdb.set_trace()
                        for icomp, comp in enumerate(parsed_component):
                            if icomp == 0:
                                component.name = comp
                            elif "!" in comp:
                                # this is a bond, we'll have to figure out how to make the bonds
                                splt = comp.split("!")
                                component.bonds += list(
                                    filter(lambda x: len(x) > 0, splt)
                                )
                            elif "~" in comp:
                                splt = comp.split("~")
                                splt = list(filter(lambda x: len(x) > 0, splt))
                                if len(splt) > 1:
                                    component.states += splt
                                else:
                                    component.state = splt[0]
                            elif "%" in comp:
                                # this is a label, need to parse this
                                pass
                        # import IPython;IPython.embed()
                        # self._label = None
                        molecule.components.append(component)
                        self.logger.debug(
                            f"split components: {split_components}", loc=log_loc
                        )
            self.logger.debug(
                f"molecule parsed: {molecule}",
                loc=log_loc,
            )
            pattern.molecules.append(molecule)
        # ship the finalized pattern object
        pattern.canonicalize()
        return pattern
