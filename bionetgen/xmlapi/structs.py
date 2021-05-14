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
    
    def gen_string(self) -> str:
        return "{} {}".format(self.name, self.value)


class Compartment(ModelObj):
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
    def __init__(self, name, otype, patterns=[]):
        super().__init__()
        self.name = name
        self.type = otype
        self.patterns = patterns
    
    def gen_string(self) -> str:
        s = "{} {}".format(self.type, self.name)
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
    def __init__(self, name, expr):
        super().__init__()
        self.name = name
        self.expr = expr
    
    def gen_string(self) -> str:
        s = "{} {}".format(self.name, self.expr)
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


# class Rules(ModelBlock):
#     '''
#     Compartments block object that contains compartments defined in the 
#     model. 

#     Item dictionary contains the name of the compartment as the name
#     and a list of the form [Dimensionality, Size, ParentCompartment] 
#     as the value.
#     '''
#     def __init__(self):
#         super().__init__()
#         self.name = "reaction rules"

#     def __str__(self):
#         block_lines = ["\nbegin {}".format(self.name)]
#         for item in self._item_dict.keys():
#             block_lines.append(str(self._item_dict[item]))
#         block_lines.append("end {}\n".format(self.name))
#         return "\n".join(block_lines)

#     def __iter__(self):
#         return self._item_dict.values().__iter__()

#     def parse_xml_block(self, block_xml):
#         if isinstance(block_xml, list):
#             for rd in block_xml:
#                 xmlobj = RuleXML(rd)
#                 self.add_item((xmlobj.name, xmlobj))
#         else:
#             xmlobj = RuleXML(block_xml)
#             self.add_item((xmlobj.name, xmlobj))
#         self.consolidate_rules()

#     def consolidate_rules(self):
#         '''
#         Generated XML only has unidirectional rules
#         and uses "_reverse_" tag to make bidirectional 
#         rules for NFSim. Take all the "_reverse_" tagged
#         rules and convert them to bidirectional rules
#         '''
#         delete_list = []
#         for item_key in self._item_dict:
#             rxn_obj  = self._item_dict[item_key]
#             if item_key.startswith("_reverse_"):
#                 # this is the reverse of another reaction
#                 reverse_of = item_key.replace("_reverse_", "")
#                 # ensure we have the original
#                 if reverse_of in self._item_dict:
#                     # make bidirectional and add rate law
#                     r1 = self._item_dict[reverse_of].rate_constants[0]
#                     r2 = rxn_obj.rate_constants[0]
#                     self._item_dict[reverse_of].set_rate_constants((r1,r2))
#                     # mark reverse for deletion
#                     delete_list.append(item_key)
#         # delete items marked for deletion
#         for del_item in delete_list:
#             self._item_dict.pop(del_item)

#     def __init__(self, pattern_xml):
#         self.bidirectional = False
#         super().__init__(pattern_xml)

#     def __iter__(self):
#         return self.iter_tpl.__iter__()

#     def gen_string(self):
#         if self.bidirectional:
#             return "{}: {} <-> {} {},{}".format(self.name, self.side_string(self.reactants), self.side_string(self.products), self.rate_constants[0], self.rate_constants[1])
#         else:
#             return "{}: {} -> {} {}".format(self.name, self.side_string(self.reactants), self.side_string(self.products), self.rate_constants[0])

#     def side_string(self, patterns):
#         side_str = ""
#         for ipat, pat in enumerate(patterns):
#             if ipat > 0:
#                 side_str += " + "
#             side_str += str(pat)
#         return side_str

#     def set_rate_constants(self, rate_cts):
#         if len(rate_cts) == 1:
#             self.rate_constants = [rate_cts[0]]
#             self.bidirectional = False
#         elif len(rate_cts) == 2: 
#             self.rate_constants = [rate_cts[0], rate_cts[1]]
#             self.bidirectional = True
#         else:
#             print("1 or 2 rate constants allowed")


