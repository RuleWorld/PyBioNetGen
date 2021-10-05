from .blocks import ParameterBlock, CompartmentBlock, ObservableBlock
from .blocks import SpeciesBlock, MoleculeTypeBlock
from .blocks import FunctionBlock, RuleBlock

from .pattern import Pattern, Molecule, Component

###### Base object  ######
class XMLObj:
    """
    Base object that contains XMLs that is the parent of
    all XML object that will be used for BNGL blocks as
    we read from BNGXML. This sets up the python internals
    such as __repr__ and __str__ for the rest of the XML
    classes.

    This base class assumes at least two methods will be
    defined by each class that inherits this base object
    which are defined in the methods below.

    Attributes
    ----------
    xml : list/OrderedDict
        XML loaded via xmltodict to be parsed. Either a
        list of items or an OrderedDict.
    parsed_obj : obj
        appropriate parsed object, one of the Block objects

    Methods
    -------
    resolve_xml(xml)
        the method that parses the XML given and is written
        separately for each subclass of this one
    gen_string()
        the method to generate the string from the parsed
        object
    """

    def __init__(self, xml):
        self.xml = xml
        self.parsed_obj = self.parse_xml(self.xml)

    def __repr__(self):
        return self.gen_string()

    def __str__(self):
        return self.gen_string()

    def gen_string(self):
        return str(self.parsed_obj)

    def parse_xml(self, xml):
        """ """
        raise NotImplementedError


###### Fundamental parsing objects ######
# This is for handling bond XMLs
class BondsXML:
    """
    Bonds XML parser, derived from XMLObj.
    """

    def __init__(self, bonds_xml=None):
        self.bonds_dict = {}
        if bonds_xml is not None:
            self.resolve_xml(bonds_xml)

    def set_xml(self, bonds_xml):
        self.resolve_xml(bonds_xml)

    def get_bond_id(self, comp):
        # Get the ID of the bond from an XML id something
        # belongs to, e.g. O1_P1_M1_C2
        num_bonds = comp["@numberOfBonds"]
        comp_id = comp["@id"]
        try:
            num_bonds = int(num_bonds)
        except:
            # This means we have something like +/?
            return num_bonds
        # use the comp_id to find the bond index from
        # self.bonds_dict
        comp_key = self.get_tpl_from_id(comp_id)
        bond_id = self.bonds_dict[comp_key]
        return bond_id

    def get_tpl_from_id(self, id_str):
        # ID str is looking like O1_P1_M2_C3
        # we are going to assume a 4-tuple per key
        id_list = id_str.split("_")
        id_tpl = tuple(id_list)
        return id_tpl

    def tpls_from_bond(self, bond):
        s1 = bond["@site1"]
        s2 = bond["@site2"]
        id_list_1 = s1.split("_")
        s1_tpl = tuple(id_list_1)
        id_list_2 = s2.split("_")
        s2_tpl = tuple(id_list_2)
        return (s1_tpl, s2_tpl)

    def resolve_xml(self, bonds_xml):
        # self.bonds_dict is a dictionary you can key
        # with the tuple taken from the ID and then
        # get a bond ID cleanly
        if isinstance(bonds_xml, list):
            for ibond, bond in enumerate(bonds_xml):
                bond_partner_1, bond_partner_2 = self.tpls_from_bond(bond)
                if bond_partner_1 not in self.bonds_dict:
                    self.bonds_dict[bond_partner_1] = [ibond + 1]
                else:
                    self.bonds_dict[bond_partner_1].append([ibond + 1])
                if bond_partner_2 not in self.bonds_dict:
                    self.bonds_dict[bond_partner_2] = [ibond + 1]
                else:
                    self.bonds_dict[bond_partner_2].append(ibond + 1)
        else:
            bond_partner_1, bond_partner_2 = self.tpls_from_bond(bonds_xml)
            self.bonds_dict[bond_partner_1] = [1]
            self.bonds_dict[bond_partner_2] = [1]


# The full pattern parser
class PatternXML(XMLObj):
    """
    Pattern XML parser, derived from XMLObj.

    Methods
    -------
    _process_mol(xml)
        processes a molecule XML dictionary and returns
        a Molecule object
    _process_comp(self, xml)
        processes a component XML dictionary and returns
        a list of Compartment objects
    """

    def __init__(self, xml) -> None:
        super().__init__(xml)

    def parse_xml(self, xml) -> Pattern:
        # initialize
        pattern = Pattern()
        if "ListOfBonds" in xml:
            # TODO: FIX THIS
            bonds = BondsXML(xml["ListOfBonds"]["Bond"])
            pattern._bonds = bonds
            self._bonds = bonds
        else:
            bonds = BondsXML()
            pattern._bonds = bonds
            self._bonds = bonds
        #
        if "@compartment" in xml:
            pattern.compartment = xml["@compartment"]
        #
        if "@label" in xml:
            pattern.label = xml["@label"]
        #
        if "@Fixed" in xml:
            if xml["@Fixed"] == "1":
                pattern.fixed = True
        #
        mols = xml["ListOfMolecules"]["Molecule"]
        molecules = []
        if isinstance(mols, list):
            # list of molecules
            for imol, mol in enumerate(mols):
                mol_obj = self._process_mol(mol)
                molecules.append(mol_obj)
        else:
            # a single molecule
            mol_obj = self._process_mol(mols)
            molecules.append(mol_obj)
        pattern.molecules = molecules
        # return a complete pattern object
        return pattern

    def _process_mol(self, xml) -> Molecule:
        """ """
        # initialize
        molecule = Molecule()
        #
        if "@name" in xml:
            molecule.name = xml["@name"]
        #
        if "@label" in xml:
            molecule.label = xml["@label"]
        #
        if "@compartment" in xml:
            molecule.compartment = xml["@compartment"]
        #
        if "ListOfComponents" in xml:
            # Single molecule can't have bonds
            molecule.components = self._process_comp(
                xml["ListOfComponents"]["Component"]
            )
        #
        return molecule

    def _process_comp(self, xml) -> list:
        # bonds = compartment id, bond id
        # comp xml can be a list or a dict
        comp_list = []
        if isinstance(xml, list):
            # we have multiple and this is a list
            for icomp, comp in enumerate(xml):
                component = Component()
                component.name = comp["@name"]
                if "@label" in comp:
                    component.label = comp["@label"]
                if "@state" in comp:
                    component.state = comp["@state"]
                if comp["@numberOfBonds"] != "0":
                    # DEBUG
                    bond_id = self._bonds.get_bond_id(comp)
                    for bi in bond_id:
                        component.bonds.append(bi)
                comp_list.append(component)
        else:
            # single comp, this is a dict
            component = Component()
            component.name = xml["@name"]
            if "@label" in xml:
                component.label = xml["@label"]
            if "@state" in xml:
                component.state = xml["@state"]
            if xml["@numberOfBonds"] != "0":
                bond_id = self._bonds.get_bond_id(xml)
                for bi in bond_id:
                    component.bonds.append(bi)
            comp_list.append(component)
        return comp_list


# Helper parser for pattern list (for observables)
class PatternListXML:
    """
    Pattern list XML parser. Takes a list of patterns
    and parses them using PatternXML and generates a
    list of patterns.

    Attributes
    ----------
    patterns : list[Pattern]
        list of patterns parsed from the XML dict list
    """

    def __init__(self, xml) -> None:
        self.patterns = self.parse_xml(xml)

    def parse_xml(self, xml) -> list:
        pats = xml["Pattern"]
        patterns = []
        if isinstance(pats, list):
            # we have multiple patterns so this is a list
            for ipattern, pattern in enumerate(pats):
                patterns.append(PatternXML(pattern).parsed_obj)
        else:
            patterns.append(PatternXML(pats).parsed_obj)
        return patterns


###### Parsers  ######
class ParameterBlockXML(XMLObj):
    """
    PatternBlock XML parser, derived from XMLObj. Creates
    a ParameterBlock that contains the parameters parsed.
    """

    def __init__(self, xml) -> None:
        super().__init__(xml)

    def parse_xml(self, xml) -> ParameterBlock:
        # make block
        block = ParameterBlock()
        # parse parameters
        if isinstance(xml, list):
            for b in xml:
                # add content to line
                name = b["@id"]
                value = b["@value"]
                expression = None
                if "@expr" in b:
                    expression = b["@expr"]
                block.add_parameter(name, value, expr=expression)
        else:
            # add content to line
            name = xml["@id"]
            value = xml["@value"]
            expression = None
            if "@expr" in xml:
                expression = xml["@expr"]
            # add to list of lines
            block.add_parameter(name, value, expr=expression)
        block.reset_compilation_tags()
        return block


#
class CompartmentBlockXML(XMLObj):
    """
    CompartmentBlock XML parser, derived from XMLObj. Creates
    a CompartmentBlock that contains the compartments parsed.
    """

    def __init__(self, xml) -> None:
        super().__init__(xml)

    def parse_xml(self, xml):
        block = CompartmentBlock()

        if isinstance(xml, list):
            for comp in xml:
                cname = comp["@id"]
                dim = comp["@spatialDimensions"]
                size = comp["@size"]
                outside = None
                if "@outside" in comp:
                    outside = comp["@outside"]
                block.add_compartment(cname, dim, size, outside=outside)
        else:
            cname = xml["@id"]
            dim = xml["@spatialDimensions"]
            size = xml["@size"]
            outside = None
            if "@outside" in xml:
                outside = xml["@outside"]
            block.add_compartment(cname, dim, size, outside=outside)

        block.reset_compilation_tags()
        return block


#
class ObservableBlockXML(XMLObj):
    """
    ObservableBlock XML parser, derived from XMLObj. Creates
    an ObservableBlock that contains the observables parsed.
    """

    def __init__(self, xml) -> None:
        super().__init__(xml)

    def parse_xml(self, xml) -> ObservableBlock:
        #
        block = ObservableBlock()
        #
        if isinstance(xml, list):
            for b in xml:
                name = b["@name"]
                otype = b["@type"]
                patterns = PatternListXML(b["ListOfPatterns"]).patterns
                block.add_observable(name, otype, patterns)
        else:
            name = xml["@name"]
            otype = xml["@type"]
            patterns = PatternListXML(xml["ListOfPatterns"]).patterns
            block.add_observable(name, otype, patterns)
        #
        return block


#
class SpeciesBlockXML(XMLObj):
    """
    SpeciesBlock XML parser, derived from XMLObj. Creates
    a SpeciesBlock that contains the species parsed.
    """

    def __init__(self, xml):
        super().__init__(xml)

    def parse_xml(self, xml):
        block = SpeciesBlock()

        if isinstance(xml, list):
            # we have multiple patterns so this is a list
            for ispec, spec in enumerate(xml):
                pattern = PatternXML(spec)
                count = spec["@concentration"]
                block.add_species(pattern, count)
        else:
            pattern = PatternXML(xml)
            count = xml["@concentration"]
            block.add_species(pattern, count)

        return block


#
class MoleculeTypeBlockXML(XMLObj):
    """
    MoleculeTypeBlock XML parser, derived from XMLObj. Creates
    a MoleculeTypeBlock that contains the molecule types parsed.

    Methods
    -------
    add_molecule_type_to_block(block,xml)
        parses the XML to create a MoleculeType object and
        adds it to a given MoleculeTypeBlock object
    """

    def __init__(self, xml):
        super().__init__(xml)

    def parse_xml(self, xml):
        block = MoleculeTypeBlock()
        #
        if isinstance(xml, list):
            for md in xml:
                self.add_molecule_type_to_block(block, md)
        else:
            self.add_molecule_type_to_block(block, xml)
        #
        return block

    def add_molecule_type_to_block(self, block, xml):
        name = xml["@id"]
        components = []
        if "ListOfComponentTypes" in xml:
            comp_obj = Component()
            comp_dict = xml["ListOfComponentTypes"]["ComponentType"]
            if "@id" in comp_dict:
                comp_obj.name = comp_dict["@id"]
                if "ListOfAllowedStates" in comp_dict:
                    # we have states
                    al_states = comp_dict["ListOfAllowedStates"]["AllowedState"]
                    if isinstance(al_states, list):
                        for istate, state in enumerate(al_states):
                            comp_obj.states.append(state["@id"])
                    else:
                        comp_obj.states.append(al_states["@id"])
                components.append(comp_obj)
            else:
                # multiple components
                for icomp, comp in enumerate(comp_dict):
                    comp_obj = Component()
                    comp_obj.name = comp["@id"]
                    if "ListOfAllowedStates" in comp:
                        # we have states
                        al_states = comp["ListOfAllowedStates"]["AllowedState"]
                        if isinstance(al_states, list):
                            for istate, state in enumerate(al_states):
                                comp_obj.states.append(state["@id"])
                        else:
                            comp_obj.states.append(al_states["@id"])
                    components.append(comp_obj)
        block.add_molecule_type(name, components)


class FunctionBlockXML(XMLObj):
    # TODO for some reason the resolve_xml doesn't set the full
    # function string and it's also not used downstream.

    """
    FunctionBlock XML parser, derived from XMLObj. Creates
    a FunctionBlock that contains the functions parsed.

    Methods
    -------
    get_arguments(xml)
        parses the argument list XML and returns a list of
        argument names
    """

    def __init__(self, xml):
        super().__init__(xml)

    def parse_xml(self, xml):
        block = FunctionBlock()
        #
        if isinstance(xml, list):
            for f in xml:
                # add content to line
                fname = f["@id"]
                expr = f["Expression"]
                args = []
                if "ListOfArguments" in f:
                    args = self.get_arguments(f["ListOfArguments"]["Argument"])
                #
                block.add_function(fname, expr, args=args)
        else:
            fname = xml["@id"]
            expr = xml["Expression"]
            args = []
            if "ListOfArguments" in xml:
                args = self.get_arguments(xml["ListOfArguments"]["Argument"])
            #
            block.add_function(fname, expr, args=args)

        return block

    def get_arguments(self, xml) -> list:
        args = []
        if isinstance(xml, list):
            for arg in xml:
                args.append(arg["@id"])
            return args
        else:
            return [xml["@id"]]


class RuleBlockXML(XMLObj):
    """
    RuleBlock XML parser, derived from XMLObj. Creates
    a RuleBlock that contains the rules parsed.

    Methods
    -------
    resolve_ratelaw(xml)
        parses a rate law XML and returns the rate constant
    resolve_rxn_side(xml)
        parses either reactants or products XML and returns
        a list of Pattern objects
    """

    def __init__(self, xml):
        self.bidirectional = False
        super().__init__(xml)

    def parse_xml(self, xml):
        block = RuleBlock()

        #
        if isinstance(xml, list):
            for irule, rule in enumerate(xml):
                name = rule["@name"]
                reactants = self.resolve_rxn_side(rule["ListOfReactantPatterns"])
                products = self.resolve_rxn_side(rule["ListOfProductPatterns"])
                if "RateLaw" not in rule:
                    print(
                        "Rule seems to be missing a rate law, please make sure that XML exporter of BNGL supports whatever you are doing!"
                    )
                rate_constants = [self.resolve_ratelaw(rule["RateLaw"])]

                block.add_rule(
                    name,
                    reactants=reactants,
                    products=products,
                    rate_constants=rate_constants,
                )
        else:
            name = xml["@name"]
            reactants = self.resolve_rxn_side(xml["ListOfReactantPatterns"])
            products = self.resolve_rxn_side(xml["ListOfProductPatterns"])
            if "RateLaw" not in xml:
                print(
                    "Rule seems to be missing a rate law, please make sure that XML exporter of BNGL supports whatever you are doing!"
                )
            rate_constants = [self.resolve_ratelaw(xml["RateLaw"])]

            block.add_rule(
                name,
                reactants=reactants,
                products=products,
                rate_constants=rate_constants,
            )
        block.consolidate_rules()
        return block

    def resolve_ratelaw(self, xml):
        rate_type = xml["@type"]
        if rate_type == "Ele":
            rate_cts_xml = xml["ListOfRateConstants"]
            rate_cts = rate_cts_xml["RateConstant"]["@value"]
        elif rate_type == "Function":
            rate_cts = xml["@name"]
        elif rate_type == "MM" or rate_type == "Sat":
            # A function type
            rate_cts = rate_type + "("
            args = xml["ListOfRateConstants"]["RateConstant"]
            if isinstance(args, list):
                for iarg, arg in enumerate(args):
                    if iarg > 0:
                        rate_cts += ","
                    rate_cts += arg["@value"]
            else:
                rate_cts += args["@value"]
            rate_cts += ")"
        else:
            print("don't recognize rate law type")
        return rate_cts

    def resolve_rxn_side(self, xml):
        # import ipdb;ipdb.set_trace()
        # this is either reactant or product
        if xml is None:
            return [Molecule()]
        elif "ReactantPattern" in xml:
            # this is a lhs/reactant side
            sl = []
            side = xml["ReactantPattern"]
            if "@compartment" in side:
                self.react_comp = side["@compartment"]
            else:
                self.react_comp = None
            if isinstance(side, list):
                # this is a list of reactant patterns
                for ireact, react in enumerate(side):
                    sl.append(PatternXML(react).parsed_obj)
            else:
                sl.append(PatternXML(side).parsed_obj)
            return sl
        elif "ProductPattern" in xml:
            # rhs/product side
            side = xml["ProductPattern"]
            sl = []
            if "@compartment" in side:
                self.prod_comp = side["@compartment"]
            else:
                self.prod_comp = None
            if isinstance(side, list):
                # this is a list of product patterns
                for iprod, prod in enumerate(side):
                    sl.append(PatternXML(prod).parsed_obj)
            else:
                sl.append(PatternXML(side).parsed_obj)
            return sl
        else:
            print("Can't parse rule XML {}".format(xml))
