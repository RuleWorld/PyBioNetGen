from .pattern import Pattern, Molecule, Component, Bonds

###### XMLObjs ###### 
class XMLObj:
    '''
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
    xml : ??
        XML string to be parsed for the block

    Methods
    -------
    resolve_xml(xml)
        the method that parses the XML associated with
        the instance and adjust is appropriately 
    gen_string()
        the method to generate the string from the information
        contained in the instance
    '''
    def __init__(self, xml):
        self.xml = xml
        self.resolve_xml(self.xml)

    def __repr__(self):
        return self.gen_string()

    def __str__(self):
        return self.gen_string()

class ObsXML(XMLObj):
    '''
    Observable XML object. Observables are a list of 
    patterns where a pattern is a list of molecules. 

    Attributes
    ----------
    patterns : list
        list of Pattern objects that make up the observable
    '''
    def __init__(self, xml):
        self.patterns = []
        super().__init__(xml)

    def __iter__(self):
        return self.patterns.__iter__()

    def __getitem__(self, key):
        return self.patterns[key]

    def gen_string(self):
        obs_str = ""
        for ipat, pat in enumerate(self.patterns):
            if ipat > 0:
                obs_str += ","
            obs_str += str(pat)
        return obs_str

    def resolve_xml(self, obs_xml):
        patterns = obs_xml['Pattern']
        if isinstance(patterns, list):
            # we have multiple patterns so this is a list
            for ipattern, pattern in enumerate(patterns): 
                # 
                self.patterns.append(Pattern(pattern))
        else:
            self.patterns.append(Pattern(patterns))

class SpeciesXML(Pattern):
    '''
    Species XML object. Species are a list of molecules. 

    Attributes
    ----------
    molecules : list
        list of molecules objects that make up the species
    '''
    def __init__(self, xml):
        self._xml = xml
        self._bonds = Bonds()
        self._label = None
        self._compartment = None
        self.molecules = []
        # sets self.molecules up 
        self._parse_xml(xml)

class MolTypeXML(XMLObj):
    '''
    Molecule Type XML object. Molecules types are like molecules
    but with multiple states for each component. 

    Attributes
    ----------
    molecule : Molecule
        a molecule object that forms this molecule type

    Methods
    -------
    add_component(name, states)
        adds component with name "name" and optional states given by 
        a list of strings
    '''
    def __init__(self, xml):
        super().__init__(xml)

    def add_component(self, name, states=None):
        self.molecule.add_component(name, states=states)

    def gen_string(self):
        return str(self.molecule)

    def resolve_xml(self, molt_xml):
        mol_obj = Molecule()
        mol_obj.name = molt_xml['@id'] 
        if 'ListOfComponentTypes' in molt_xml:
            comp_obj = Component()
            comp_dict = molt_xml['ListOfComponentTypes']['ComponentType']
            if '@id' in comp_dict:
                comp_obj.name = comp_dict["@id"]
                if "ListOfAllowedStates" in comp_dict:
                    # we have states
                    al_states = comp_dict['ListOfAllowedStates']['AllowedState']
                    if isinstance(al_states, list):
                        for istate, state in enumerate(al_states):
                            comp_obj.states.append(state["@id"])
                    else:
                        comp_obj.states.append(state["@id"])
                mol_obj.components.append(comp_obj)
            else:
                # multiple components
                for icomp, comp in enumerate(comp_dict):
                    comp_obj = Component()
                    comp_obj.name = comp['@id']
                    if "ListOfAllowedStates" in comp:
                        # we have states
                        al_states = comp['ListOfAllowedStates']['AllowedState']
                        if isinstance(al_states, list):
                            for istate, state in enumerate(al_states):
                                comp_obj.states.append(state['@id'])
                        else:
                            comp_obj.states.append(al_states['@id'])
                    mol_obj.components.append(comp_obj)
        self.molecule = mol_obj

class RuleXML(XMLObj):
    '''
    Molecule Type XML object. Molecules types are like molecules
    but with multiple states for each component. 

        A rule is a tuple (list of reactant patterns, list of 
    product patterns, list of rate constant functions)

    Attributes
    ----------
    bidirectoinal : boolean
        list of molecules objects that make up the species
    name : str
        name of the rule, if exists
    reactants : list[Pattern]
        list of patterns that form the reactant side of the rule
    products : list[Pattern]
        List of patterns that form the products side of the rule
    rate_constants : list[Str]
        list of 1 or 2 rate constants

    Methods
    -------
    side_string(name, states)
        gets the string for a side of the reaction, given a list of pattern objects
    set_rate_constants(rate_cts)
        takes an iterable of 1 or 2 rate constants and adjust the object
        and sets bidirectionality
    resolve_rate_law(rate_xml)
        parses XML for rate constants and adds it to the object
    resolve_rxn_side(side_xml)
        parses the XML for either reactants or products and adds it to 
        the object
    '''
    def __init__(self, pattern_xml):
        self.bidirectional = False
        super().__init__(pattern_xml)

    def __iter__(self):
        return self.iter_tpl.__iter__()

    def gen_string(self):
        if self.bidirectional:
            return "{}: {} <-> {} {},{}".format(self.name, self.side_string(self.reactants), self.side_string(self.products), self.rate_constants[0], self.rate_constants[1])
        else:
            return "{}: {} -> {} {}".format(self.name, self.side_string(self.reactants), self.side_string(self.products), self.rate_constants[0])

    def side_string(self, patterns):
        side_str = ""
        for ipat, pat in enumerate(patterns):
            if ipat > 0:
                side_str += " + "
            side_str += str(pat)
        return side_str

    def set_rate_constants(self, rate_cts):
        if len(rate_cts) == 1:
            self.rate_constants = [rate_cts[0]]
            self.bidirectional = False
        elif len(rate_cts) == 2: 
            self.rate_constants = [rate_cts[0], rate_cts[1]]
            self.bidirectional = True
        else:
            print("1 or 2 rate constants allowed")
    
    def resolve_xml(self, pattern_xml):
        # 
        rule_name = pattern_xml['@name']
        self.name = rule_name
        self.reactants = self.resolve_rxn_side(pattern_xml['ListOfReactantPatterns'])
        self.products = self.resolve_rxn_side(pattern_xml['ListOfProductPatterns'])
        if 'RateLaw' not in pattern_xml:
            print("Rule seems to be missing a rate law, please make sure that XML exporter of BNGL supports whatever you are doing!")
        self.rate_constants = [self.resolve_ratelaw(pattern_xml['RateLaw'])]
        self.rule_tpl = (self.reactants, self.products, self.rate_constants)

    def resolve_ratelaw(self, rate_xml):
        rate_type = rate_xml['@type']
        if rate_type == 'Ele':
            rate_cts_xml = rate_xml['ListOfRateConstants']
            rate_cts = rate_cts_xml['RateConstant']['@value']
        elif rate_type == 'Function':
            rate_cts = rate_xml['@name']
        elif rate_type == 'MM' or rate_type == "Sat":
            # A function type 
            rate_cts = rate_type + "("
            args = rate_xml['ListOfRateConstants']["RateConstant"]
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

    def resolve_rxn_side(self, side_xml):
        # this is either reactant or product
        if side_xml is None:
            return [Molecule()]
        elif 'ReactantPattern' in side_xml:
            # this is a lhs/reactant side
            sl = []
            side = side_xml['ReactantPattern']
            if '@compartment' in side:
                self.react_comp = side['@compartment']
            else:
                self.react_comp = None
            if isinstance(side, list):
                # this is a list of reactant patterns
                for ireact, react in enumerate(side):
                    sl.append(Pattern(react))
            else: 
                sl.append(Pattern(side))
            return sl
        elif "ProductPattern" in side_xml:
            # rhs/product side
            side = side_xml['ProductPattern']
            sl = []
            if '@compartment' in side:
                self.prod_comp = side['@compartment']
            else:
                self.prod_comp = None
            if isinstance(side, list):
                # this is a list of product patterns
                for iprod, prod in enumerate(side):
                    sl.append(Pattern(prod))
            else: 
                sl.append(Pattern(side))
            return sl
        else: 
            print("Can't parse rule XML {}".format(side_xml))

class FuncXML(XMLObj):
    # TODO for some reason the resolve_xml doesn't set the full
    # function string and it's also not used downstream. 

    '''
    Function XML object. Functions are expressions and IDs which 
    is the name of the function with potential arguments. 

    Attributes
    ----------
    item_tuple
        tuple of (function_str, expression) where function_str is the 
        string that forms the name + arguments of the function (e.g. g(x))
        and expression is the definition of the function.
    
    Methods
    -------
    get_arguments(arg_xml)
        given the XML of arguments, this methods pulls out the list of 
        arguments the function needs and returns a list of strings. 
    '''
    def __init__(self, pattern_xml):
        super().__init__(pattern_xml)

    def resolve_xml(self, func_xml):
        fname = func_xml['@id']
        expression = func_xml['Expression']
        args = []
        if 'ListOfArguments' in func_xml:
            args = self.get_arguments(func_xml['ListOfArguments']['Argument'])
        expr = func_xml['Expression']
        func_str = fname + "("
        if len(args) > 0:
            for iarg, arg in enumerate(args):
                if iarg > 0:
                    func_str += ","
                func_str += arg
        func_str += ")"
        self.item_tuple = (func_str, expression)
        full_str = "{} = {}".format(func_str, expression)
        return full_str 

    def get_arguments(self, arg_xml):
        args = []
        if isinstance(arg_xml, list):
            for arg in arg_xml:
                args.append(arg['@id'])
            return args
        else:
            return [arg_xml['@id']]
###### PATTERNS ###### 
