from bionetgen.modelapi.pattern import Molecule, Pattern


class ModelObj:
    """
    The base class for all items in a model (parameter, observable etc.).

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
        self._comment = None
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
    def comment(self, val) -> str:
        # TODO: regex handling of # instead
        if val.startswith("#"):
            self._comment = val[1:]
        else:
            self._comment = val

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


class Parameter(ModelObj):
    """
    Class for all parameters in the model, subclass of ModelObj.

    In BNGL parameters are of the form
        parameter_name parameter_value/expression
    or
        parameter_name = parameter_value/expression

    Attributes
    ----------
    name : str
        name of the parameter
    value : str
        value of the parameter, if loaded from XML this will always
        exist since NFsim needs the value and not the expression
    expr : str
        this exists if the parameter is a math expression, not necerssary
    write_expr : bool
        this is a boolean that determines if the generated string has
        is in expression form or in value form.
    """

    def __init__(self, name, value, expr=None):
        super().__init__()
        self.name = name
        self.value = value
        self.expr = expr
        try:
            test = float(expr)
            self.write_expr = False
        except:
            self.write_expr = True

    def gen_string(self) -> str:
        if self.write_expr:
            return "{} {}".format(self.name, self.expr)
        else:
            return "{} {}".format(self.name, self.value)


class Compartment(ModelObj):
    """
    Class for all compartments in the model, subclass of ModelObj.

    In BNGL the compartments are of the form
        compartment_name dimensions size
    or
        compartment_name dimensions size parent_compartment
    the second form only applies when one compartment is contained in
    another compartment.

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
    write_expr : bool
        boolean that describes if the size is a volume or an expression
    """

    def __init__(self, name, dim, size, outside=None):
        super().__init__()
        self.name = name
        self.dim = dim
        self.size = size
        try:
            test = float(size)
            self.write_expr = False
        except:
            self.write_expr = True
        self.outside = outside

    def gen_string(self) -> str:
        s = "{} {} {}".format(self.name, self.dim, self.size)
        if self.outside is not None:
            s += " {}".format(self.outside)
        return s


class Observable(ModelObj):
    """
    Class for all observable in the model, subclass of ModelObj.

    In BNGL the observables are of the form
        observable_type observable_name observable_patterns
    where patterns can include multiple patterns separated by commas.

    Attributes
    ----------
    name : str
        name of the observable
    type : str
        type of the observable, Molecules or Species
    patterns : list[Pattern]
        list of patterns of the observable

    Methods
    -------
    add_pattern
        add a Pattern object into the list of patterns
        for this observable
    """

    def __init__(self, name, otype, patterns=[]):
        super().__init__()
        self.name = name
        self.type = otype
        self.patterns = patterns

    def gen_string(self) -> str:
        s = "{} {} ".format(self.type, self.name)
        for ipat, pat in enumerate(self.patterns):
            if ipat > 0:
                s += ","
            s += str(pat)
        return s

    def add_pattern(self, pat) -> None:
        self.patterns.append(pat)


class MoleculeType(ModelObj):
    """
    Class for all parameters in the model, subclass of ModelObj.

    In BNGL the molecule types are of the form
        molecule_type
    where all possible states of each component of a molecule is
    listed, e.g.
        A(b, p~0~1, k~ON~OFF~NULL)

    Attributes
    ----------
    molecule : Molecule
        a molecule type only contains a molecule object which
        can also handle multiple component states
    """

    def __init__(self, name, components):
        super().__init__()
        self.name = name
        self.molecule = Molecule(name=name, components=components)

    def gen_string(self) -> str:
        return str(self.molecule)


class Species(ModelObj):
    """
    Class for all parameters in the model, subclass of ModelObj.

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

    def __init__(self, pattern=Pattern(), count=0):
        super().__init__()
        self.pattern = pattern
        self.count = count
        self.name = str(self.pattern)

    def gen_string(self) -> str:
        s = "{} {}".format(self.pattern, self.count)
        return s


class Function(ModelObj):
    """
    Class for all parameters in the model, subclass of ModelObj.

    In BNGL functions are of the form
        function_name function_expression
    or
        function_name = function_expression
    and functions can have arguments
        function_name(arg1, arg2, ..., argN)


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


class Action(ModelObj):
    """
    Class for all parameters in the model, subclass of ModelObj.

    In BNGL actions are of the form
        action_type({arg1=>value1, arg2=>value2, ...})

    Attributes
    ----------
    type : str
        type of action, e.g. simulate or writeFile
    args : list[(arg_name,arg_value)]
        (argument,value) pair list for the action
    """

    def __init__(self, action_type=None, action_args=[]) -> None:
        super().__init__()
        self.type = action_type
        self.args = action_args

    def gen_string(self) -> str:
        # TODO: figure out every argument that has special
        # requirements, e.g. method requires the value to
        # be a string
        action_str = "{}(".format(self.type) + "{"
        for iarg, arg in enumerate(self.args):
            val = arg[1]
            arg = arg[0]
            if iarg > 0:
                action_str += ","
            if arg == "method":
                action_str += '{}=>"{}"'.format(arg, val)
            else:
                action_str += "{}=>{}".format(arg, val)
        action_str += "})"
        return action_str

    def print_line(self) -> str:
        s = ""
        # let's deal with line label
        if self.line_label is not None:
            s += self.line_label
        # start building the rest of the string
        s += str(self)
        if self.comment is not None:
            s += " #{}".format(self.comment)
        return s


class Rule(ModelObj):
    """
    Class for all parameters in the model, subclass of ModelObj.

    Attributes
    ----------
    name : str
        name of the rule, optional
    reactants : list[Pattern]
        list of patterns for reactants
    products : list[Pattern]
        list of patterns for products

    Methods
    -------
    set_rate_constants((k_fwd,k_bck))
        sets forward and backwards rate constants, backwards rate
        constants are optional and if not given, will set the rule
        to be a unidirectional rule
    side_string(list[Pattern])
        given a list of patterns, return a string formatted to be
        on one side of a rule definition
    """

    def __init__(self, name, reactants=[], products=[], rate_constants=()) -> None:
        super().__init__()
        self.name = name
        self.reactants = reactants
        self.products = products
        self.set_rate_constants(rate_constants)

    def set_rate_constants(self, rate_cts):
        if len(rate_cts) == 1:
            self.rate_constants = [rate_cts[0]]
            self.bidirectional = False
        elif len(rate_cts) == 2:
            self.rate_constants = [rate_cts[0], rate_cts[1]]
            self.bidirectional = True
        else:
            print("1 or 2 rate constants allowed")

    def gen_string(self):
        if self.bidirectional:
            return "{}: {} <-> {} {},{}".format(
                self.name,
                self.side_string(self.reactants),
                self.side_string(self.products),
                self.rate_constants[0],
                self.rate_constants[1],
            )
        else:
            return "{}: {} -> {} {}".format(
                self.name,
                self.side_string(self.reactants),
                self.side_string(self.products),
                self.rate_constants[0],
            )

    def side_string(self, patterns):
        side_str = ""
        for ipat, pat in enumerate(patterns):
            if ipat > 0:
                side_str += " + "
            side_str += str(pat)
        return side_str
