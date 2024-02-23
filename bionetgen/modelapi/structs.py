from bionetgen.modelapi.pattern import Molecule, Pattern
from bionetgen.modelapi.rulemod import RuleMod
from bionetgen.core.utils.utils import ActionList
from bionetgen.core.exc import BNGParseError


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
    def comment(self, val) -> None:
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
    """

    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value

    def gen_string(self) -> str:
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


class Observable(ModelObj):
    """
    Class for all observables in the model, subclass of ModelObj.

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
        if self.type == "Species":
            for pat in patterns:
                if pat.MatchOnce:
                    pat.MatchOnce = False
        self.patterns = patterns

    def gen_string(self) -> str:
        s = "{} {} ".format(self.type, self.name)
        for ipat, pat in enumerate(self.patterns):
            if ipat > 0:
                s += ","
            s += str(pat)
        return s

    def add_pattern(self, pat) -> None:
        # if type is species, set MatchOnce to false since all species automatically match once
        if self.type == "Species":
            pat.MatchOnce = False
        self.patterns.append(pat)


class MoleculeType(ModelObj):
    """
    Class for all molecule types in the model, subclass of ModelObj.

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
    Class for all species in the model, subclass of ModelObj.

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
    Class for all functions in the model, subclass of ModelObj.

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
    Class for all actions in the model, subclass of ModelObj.

    In BNGL actions are of the form
        action_type({arg1=>value1, arg2=>value2, ...})

    Attributes
    ----------
    type : str
        type of action, e.g. simulate or writeFile
    args : dict[arg_name] = arg_value
        action arguments as keys and their values as values
    """

    def __init__(self, action_type=None, action_args={}) -> None:
        super().__init__()
        AList = ActionList()
        self.normal_types = AList.normal_types
        self.no_setter_syntax = AList.no_setter_syntax
        self.square_braces = AList.square_braces
        self.possible_types = AList.possible_types
        # Set initial values
        self.name = action_type
        self.type = action_type
        self.args = action_args
        # check type
        if self.type not in self.possible_types:
            raise BNGParseError(message=f"Action type {self.type} not recognized!")
        seen_args = []
        for arg in action_args:
            arg_name, arg_value = arg, action_args[arg]
            valid_arg_list = AList.arg_dict[self.type]
            # TODO: actions that don't take argument names should be parsed separately to check validity of arg-val tuples
            # TODO: currently not type checking arguments
            if valid_arg_list is None:
                raise BNGParseError(
                    message=f"Argument {arg_name} is given, but action {self.type} does not take arguments"
                )
            if len(valid_arg_list) > 0:
                if arg_name not in AList.arg_dict[self.type]:
                    raise BNGParseError(
                        message=f"Action argument {arg_name} not recognized!\nCheck to make sure action is correctly formatted"
                    )
                # TODO: If arg_value is the correct type
            if arg_name in seen_args:
                print(
                    f"Warning: argument {arg_name} already given, using latter value {arg_value}"
                )
            else:
                seen_args.append(arg_name)

    def gen_string(self) -> str:
        # TODO: figure out every argument that has special
        # requirements, e.g. method requires the value to
        # be a string
        action_str = "{}(".format(self.type)
        # we can skip curly if we don't have arguments
        # and we NEED to skip it for some actions
        if self.type in self.normal_types and not len(self.args) == 0:
            action_str += "{"
        elif self.type in self.square_braces:
            action_str += "["
        # add arguments
        for iarg, arg in enumerate(self.args):
            val = self.args[arg]
            if iarg > 0:
                action_str += ","
            # some actions need =>, some don't
            if self.type in self.normal_types:
                action_str += f"{arg}=>{val}"
            else:
                action_str += f"{arg}"
        # we can skip curly if we don't have arguments
        # and we NEED to skip it for some actions
        if self.type in self.normal_types and not len(self.args) == 0:
            action_str += "}"
        elif self.type in self.square_braces:
            action_str += "]"
        # close up the action
        action_str += ")"
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
    Class for all rules in the model, subclass of ModelObj.

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

    def __init__(
        self,
        name,
        reactants=[],
        products=[],
        rate_constants=(),
        rule_mod=RuleMod(),
        operations=[],
    ) -> None:
        super().__init__()
        self.name = name
        self.reactants = reactants
        self.products = products
        if rule_mod is None:
            self.rule_mod = RuleMod()
        else:
            self.rule_mod = rule_mod
        self.operations = operations
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
            return "{}: {} <-> {} {},{} {}".format(
                self.name,
                self.side_string(self.reactants),
                self.side_string(self.products),
                self.rate_constants[0],
                self.rate_constants[1],
                str(self.rule_mod),
            )
        else:
            return "{}: {} -> {} {} {}".format(
                self.name,
                self.side_string(self.reactants),
                self.side_string(self.products),
                self.rate_constants[0],
                str(self.rule_mod),
            )

    def side_string(self, patterns):
        side_str = ""
        for ipat, pat in enumerate(patterns):
            if ipat > 0:
                side_str += " + "
            side_str += str(pat)
        return side_str


class EnergyPattern(ModelObj):
    """
    Class for all energy patterns in the model, subclass of ModelObj.

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


class PopulationMap(ModelObj):
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
