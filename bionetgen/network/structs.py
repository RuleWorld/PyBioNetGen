class NetworkObj:
    """
    The base class for all items in a network object (parameter, groups etc.).

    Attributes
    ----------
    comment : str
        comment at the end of the line/object
    line_label : str
        line label at the beginning of the line/object

    Methods
    -------
    print_line()
        generates the actual line string with line label and comments
        if applicable
    gen_string()
        generates the BNGL string of the object itself, separate from
        line attributes
    """

    def __init__(self):
        self._comment = ""
        self._line_label = None

    def __str__(self) -> str:
        return self.gen_string()

    def __repr__(self) -> str:
        return self.gen_string()

    def __contains__(self, key):
        return hasattr(self, key)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __delitem__(self, key):
        delattr(self, key)

    @property
    def comment(self) -> None:
        return self._comment

    @comment.setter
    def comment(self, val) -> None:
        # TODO: regex handling of # instead
        if val is not None:
            if len(val) > 0:
                if val.startswith("#"):
                    self._comment = val[1:]
                else:
                    self._comment = val
            else:
                self._comment = None
        else:
            self._comment = None

    @property
    def line_label(self) -> str:
        return self._line_label

    @line_label.setter
    def line_label(self, val) -> None:
        # TODO: specific error handling
        try:
            ll = int(val)
            self._line_label = "{} ".format(ll)
        except:
            self._line_label = "{}: ".format(val)

    def print_line(self) -> str:
        s = "  "
        # let's deal with line label
        if self.line_label is not None:
            s += self.line_label
        # start building the rest of the string
        s += str(self)
        if self.comment is not None:
            s += " #{}".format(self.comment)
        return s


class NetworkParameter(NetworkObj):
    """
    Class for all parameters in the network, subclass of NetworkObj.

    In BNGL networks parameters are of the form
        parameter_ID parameter_name parameter_value/expression # comment

    Attributes
    ----------
    id : int
        ID/line label of the network parameter
    name : str
        name of the network parameter
    value : str
        value of the network parameter
    """

    def __init__(self, pid, name, value, comment=""):
        super().__init__()
        self.line_label = pid
        self.name = name
        self.value = value
        self.comment = comment

    def gen_string(self) -> str:
        s = "{} {}".format(self.name, self.value)
        return s


# TODO:
class NetworkCompartment(NetworkObj):
    """
    Class for all compartments in the network, subclass of NetworkObj.

    In BNGL the compartments are of the form
        compartment_name dimensions size

    Attributes
    ----------
    name : str
        name of the compartment
    dim : str
        dimensionality of the compartment
    size : str
        size/volume of the compartment
    outside : str
        parent compartment, if exists
    """

    def __init__(self, name, dim, size, outside=None):
        super().__init__()
        self.name = name
        self.dim = dim
        self.size = size
        self.outside = outside

    def gen_string(self) -> str:
        s = "{} {} {}".format(self.name, self.dim, self.size)
        if self.outside is not None:
            s += " {}".format(self.outside)
        return s


class NetworkGroup(NetworkObj):
    """
    Class for all groups in the network, subclass of NetworkObj.

    In BNGL networks the groups are of the form
        group_ID group_name group_species
    where species are separated by commas.

    Attributes
    ----------
    id : str
        id of the group
    name : str
        name of the group
    species : list[expr]
        list of species expressions of the group
    """

    def __init__(self, gid, name, members=[], comment=""):
        super().__init__()
        self.line_label = gid
        self.name = name
        self.members = members
        self.comment = comment

    def gen_string(self) -> str:
        s = "{} {} ".format(self.name, ",".join(self.members))
        return s


class NetworkSpecies(NetworkObj):
    """
    Class for all species in the network, subclass of NetworkObj.

    In BNGL the species/seed species are of the form
        species count
    where species is a single pattern and count is the starting
    value for that specific pattern

    Attributes
    ----------
    pattern : Pattern
        pattern of the seed species
    count : str
        starting value of the seed species
    """

    def __init__(self, sid, name, count=0, comment=""):
        super().__init__()
        self.line_label = sid
        self.name = name
        self.count = count
        self.comment = comment

    def gen_string(self) -> str:
        s = "{} {}".format(self.name, self.count)
        return s


# TODO:
class NetworkFunction(NetworkObj):
    """
    Class for all functions in the network, subclass of NetworkObj.

    In BNGL functions are of the form
        function_name function_expression

    Attributes
    ----------
    name : str
        name of the function
    expr : str
        function expression
    args : list
        optional list of arguments for the function
    """

    def __init__(self, name, expr, args=None):
        super().__init__()
        self.name = name
        self.expr = expr
        self.args = args

    def gen_string(self) -> str:
        if self.args is None:
            s = "{} = {}".format(self.name, self.expr)
        else:
            s = "{}({}) = {}".format(self.name, ",".join(self.args), self.expr)
        return s


# TODO:
class NetworkReaction(NetworkObj):
    """
    Class for all reactions in the network, subclass of NetworkObj.

    Attributes
    ----------
    name : str
        name of the rule, optional
    reactants : list[Pattern]
        list of patterns for reactants
    products : list[Pattern]
        list of patterns for products
    rule_mod : RuleMod
        modifier (moveConnected, TotalRate, etc.) used by a given rule
    operations : list[Operation]
        list of operations
    """

    def __init__(
        self,
        rid,
        reactants=[],
        products=[],
        rate_constant=None,
        comment=None,
    ) -> None:
        super().__init__()
        self.line_label = rid
        self.name = rid
        self.reactants = reactants
        self.products = products
        self.rate_constant = rate_constant
        self.comment = comment

    def gen_string(self):
        s = f"{','.join(self.reactants)} {','.join(self.products)} {self.rate_constant}"
        return s


# TODO:
class NetworkEnergyPattern(NetworkObj):
    """
    Class for all energy patterns in the network, subclass of NetworkObj.

    In BNGL the energy patterns are of the form
        EP_pattern EP_expression

    Attributes
    ----------
    name : str
        id of the energy pattern
    pattern : Pattern
        Pattern object representing the energy pattern
    expression : str
        expression used for energy pattern
    """

    def __init__(self, name, pattern, expression):
        super().__init__()
        self.name = name
        self.pattern = pattern
        self.expression = expression

    def gen_string(self) -> str:
        s = "{} {}".format(self.pattern, self.expression)
        return s


# TODO:
class NetworkPopulationMap(NetworkObj):
    """
    Class for all population maps in the model, subclass of ModelObj.

    In BNGL the population maps are of the form
        structured_species -> population_species lumping_parameter

    Attributes
    ----------
    name : str
        id of the population map
    struct_species : Pattern
        Pattern object representing the species to be mapped
    pop_species : Pattern
        Pattern object representing the population count
    rate : str
        lumping parameter used in population mapping
    """

    def __init__(self, name, struct_species, pop_species, rate):
        super().__init__()
        self.name = name
        self.species = struct_species
        self.population = pop_species
        self.rate = rate

    def gen_string(self) -> str:
        s = "{} -> {} {}".format(self.species, self.population, self.rate)
        return s
