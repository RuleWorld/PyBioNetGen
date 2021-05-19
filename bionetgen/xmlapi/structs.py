from bionetgen.xmlapi.pattern import Molecule, Pattern

class ModelObj:
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
    def __init__(self, name, components):
        super().__init__()
        self.molecule = Molecule(name=name, components=components)
    
    def gen_string(self) -> str:
        return str(self.molecule)
    

class Species(ModelObj):
    def __init__(self, pattern=Pattern(), count=0):
        super().__init__()
        self.pattern = pattern
        self.count = count
    
    def gen_string(self) -> str:
        s = "{} {}".format(self.pattern, self.count)
        return s


class Function(ModelObj):
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
    '''
    Action object

    Attributes
    ----------
    type
    args

    '''
    def __init__(self, action_type=None, action_args=[]) -> None:
        super().__init__()
        self.type = action_type
        self.args = action_args

    def gen_string(self) -> str:
        # TODO: figure out every argument that has special 
        # requirements, e.g. method requires the value to 
        # be a string
        action_str = "{}(".format(self.type) + "{"
        for iarg,arg in enumerate(self.args):
            val = arg[1]
            arg = arg[0]
            if iarg > 0:
                action_str += ","
            if arg == "method":
                action_str += '{}=>"{}"'.format(arg, val)
            else:
                action_str += '{}=>{}'.format(arg, val)
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
    '''
    Rule obj
    '''
    # def add_rule(self, name, reactants, products, rate_constants):

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
            return "{}: {} <-> {} {},{}".format(self.name, 
                self.side_string(self.reactants), self.side_string(self.products), 
                self.rate_constants[0], self.rate_constants[1])
        else:
            return "{}: {} -> {} {}".format(self.name, 
                self.side_string(self.reactants), self.side_string(self.products), 
                self.rate_constants[0])

    def side_string(self, patterns):
        side_str = ""
        for ipat, pat in enumerate(patterns):
            if ipat > 0:
                side_str += " + "
            side_str += str(pat)
        return side_str