# New objects
from typing import Sized


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

# ###### STRUCTS OBJECTS ###### 
# class ModelBlock:
#     '''
#     Base block object that will be used for each block in BNGL.

#     Attributes
#     ----------
#     name : str
#         Name of the block which will be used to write the BNGL text
#     lines : list
#         List of lines in each block

#     Methods
#     -------
#     reset_compilation_tags()
#         resets _recompile and _changes tag for the block
#     add_item(item_tpl)
#         while every block can implement their own add_item method
#         the base assumption that each element has a name and value
#         so this method takes in (name,value) tuple and sets 
#         _item_dict[name] = value
#     add_items(item_list)
#         loops over every element in the list and uses add_item on it
#     print
#         prints the block, uses __str__ to get the string
#     parse_xml_block(xml)
#         while it's not implemented for the base class, each block object
#         needs to implement this method where it takes in BNGXML for the 
#         block as argument and modifies the object correctly.
#     '''
#     def __init__(self):
#         self.name = "ModelBlock"
#         self.lines = OrderedDict()

#     def __len__(self):
#         return len(self.lines)

#     def __repr__(self):
#         # overwrites what the class representation
#         # shows the items in the model block in 
#         # say ipython
#         return str(self.lines)

#     def __getitem__(self, key):
#         if isinstance(key, int):
#             # get the item in order
#             return list(self.lines.keys())[key]
#         return self.lines[key]

#     def __setitem__(self, key, value):
#         self.lines[key] = value

#     def __delitem__(self, key):
#         if key in self.lines:
#             self.lines.pop(key)
#         else: 
#             print("Item {} not found".format(key))

#     def __iter__(self):
#         return self.lines.keys().__iter__()

#     def __contains__(self, key):
#         return key in self.lines
    
#     def reset_compilation_tags(self):
#         # TODO: Make these properties such that it checks each 
#         # line for changes/recompile tags
#         for line in self.lines:
#             line._recompile = False
#             line._changes = {}
    
#     def add_item(self, item_tpl):
#         # TODO: try adding evaluation of the parameter here
#         # for the future, in case we want people to be able
#         # to adjust the math
#         # TODO: Error handling, some names will definitely break this
#         name, value = item_tpl
#         self.lines[name] = value
#         try:
#             setattr(self, name, value)
#         except:
#             print("can't set {} to {}".format(name, value))
#             pass
#         self._recompile = True

#     def add_items(self, item_list):
#         for item in item_list:
#             self.add_item(item)

#     def print(self):
#         print(self)

# # TODO: Add a LOT of error handling
# class Parameters(ModelBlock):
#     '''
#     Parameter block object that contains both the expressions and values
#     for each parameter defined in the model

#     Attributes
#     ----------
#     expressions : Dict
#         this contains the expressions for each item in the block dictionary
#     values : dict
#         values of each parameter defined in the model
#     '''
#     def __init__(self):
#         self.expressions = {}
#         self.values = {}
#         super().__init__()
#         self.name = "parameters"

#     def __setattr__(self, name, value):
#         changed = False
#         if hasattr(self, "_item_dict"):
#             if name in self._item_dict.keys():
#                 try: 
#                     new_value = float(value)
#                     changed = True
#                     self._item_dict[name] = new_value
#                 except:
#                     self._item_dict[name] = value
#         if changed:
#             self._changes[name] = new_value
#             self.__dict__[name] = new_value
#         else:
#             self.__dict__[name] = value

#     def __str__(self):
#         # overwrites what the method returns when 
#         # it's converted to string
#         block_lines = ["\nbegin {}".format(self.name)]
#         for item in self._item_dict.keys():
#             block_lines.append("  " + "{} {}".format(item, self._item_dict[item]))
#         block_lines.append("end {}\n".format(self.name))
#         return "\n".join(block_lines)

#     def add_item(self, item_tpl):
#         name, value = item_tpl
#         self._item_dict[name] = value
#         try:
#             setattr(self, name, value)
#         except:
#             print("can't set {} to {}".format(name, value))
#             pass
#         self._recompile = True

# class Compartments(ModelBlock):
#     '''
#     Compartments block object that contains compartments defined in the 
#     model. 

#     Item dictionary contains the name of the compartment as the name
#     and a list of the form [Dimensionality, Size, ParentCompartment] 
#     as the value.
#     '''
#     def __init__(self):
#         super().__init__()
#         self.name = "compartments"

#     def __str__(self):
#         # overwrites what the method returns when 
#         # it's converted to string
#         block_lines = ["\nbegin {}".format(self.name)]
#         for item in self._item_dict.keys():
#             comp_line = "  {} {} {}".format(item, 
#                             self._item_dict[item][0],
#                             self._item_dict[item][1])
#             if self._item_dict[item][2] is not None:
#                 comp_line += " {}".format(self._item_dict[item][2])
#             block_lines.append(comp_line)
#         block_lines.append("end {}\n".format(self.name))
#         return "\n".join(block_lines)

#     def add_item(self, item_tpl):
#         name, dim, size, outside = item_tpl
#         self._recompile = True
#         self._item_dict[name] = [dim, size, outside]

#     def parse_xml_block(self, block_xml):


# class Observables(ModelBlock):
#     '''
#     Observable block object that contains observables defined in the 
#     model. 

#     Item dictionary contains the name of the observable as the name
#     and a list of the form [ObservableType, ObservableObject] as value. 
#     '''
#     def __init__(self):
#         super().__init__()
#         self.name = "observables"

#     def __setattr__(self, name, value):
#         if hasattr(self, "_item_dict"):
#             if name in self._item_dict.keys():
#                 self._recompile = True
#                 self._changes[name] = value
#                 self._item_dict[name][1] = value
#         self.__dict__[name] = value

#     def add_item(self, item_tpl): 
#         otype, name, obj = item_tpl
#         self._item_dict[name] = [otype, obj]
#         try:
#             setattr(self, name, obj)
#         except:
#             print("can't set {} to {}".format(name, obj))
#             pass
#         self._recompile = True

#     def __str__(self):
#         # overwrites what the method returns when 
#         # it's converted to string
#         block_lines = ["\nbegin {}".format(self.name)]
#         for item in self._item_dict.keys():
#             block_lines.append("  " + 
#                     "{} {} {}".format(self._item_dict[item][0],
#                                       item,
#                                       self._item_dict[item][1]))
#         block_lines.append("end {}\n".format(self.name))
#         return "\n".join(block_lines)

#     def __getitem__(self, key):
#         if isinstance(key, int):
#             # get the item in order
#             return self._item_dict[list(self._item_dict.keys())[key]][1]
#         return self._item_dict[key]

#     def parse_xml_block(self, block_xml):
#         #
#         if isinstance(block_xml, list):
#             for b in block_xml:
#                 xmlobj = ObsXML(b['ListOfPatterns'])
#                 self.add_item((b['@type'], b['@name'], xmlobj))
#         else: 
#             xmlobj = ObsXML(block_xml['ListOfPatterns'])
#             self.add_item((block_xml['@type'], block_xml['@name'], xmlobj))
    
#     def gen_string(self):
#         obs_str = ""
#         for ipat, pat in enumerate(self.patterns):
#             if ipat > 0:
#                 obs_str += ","
#             obs_str += str(pat)
#         return obs_str
#         # 

# class Species(ModelBlock):
#     '''
#     Species block object that contains starting species values defined
#     in the model

#     Item dictionary contains the Species object as the name and the 
#     concentration as the value so outside of parsing this is basically 
#     the same as the base object.
#     '''
#     def __init__(self):
#         super().__init__()
#         self.name = "species"

#     def __str__(self):
#         # overwrites what the method returns when 
#         # it's converted to string
#         block_lines = ["\nbegin {}".format(self.name)]
#         for item in self._item_dict.keys():
#             block_lines.append("  " + "{} {}".format(item,self._item_dict[item]))
#         block_lines.append("end {}\n".format(self.name))
#         return "\n".join(block_lines)

#     def __getitem__(self, key):
#         if isinstance(key, str):
#             # our keys are objects
#             for ikey in self._item_dict:
#                 if key == str(ikey):
#                     return self._item_dict[ikey]
#         if isinstance(key, int):
#             # get the item in order
#             return list(self._item_dict.keys())[key]
#         return self._item_dict[key]

#     def __setitem__(self, key, value):
#         if isinstance(key, str):
#             for ikey in self._item_dict:
#                 if key == str(ikey):
#                     self._item_dict[ikey] = value
#             return
#         if isinstance(key, int):
#             k = list(self._item_dict.keys())[key]
#             self._item_dict[k] = value
#             return
#         self._recompile = True
#         self._item_dict[key] = value

#     def __contains__(self, key):
#         for ikey in self._item_dict:
#             if key == str(ikey):
#                 return True
#         return False

#     def parse_xml_block(self, block_xml):
#         if isinstance(block_xml, list):
#             for sd in block_xml:
#                 xmlobj = SpeciesXML(sd)
#                 self.add_item((xmlobj,sd['@concentration']))
#         else:
#             xmlobj = SpeciesXML(block_xml)
#             self.add_item((xmlobj,block_xml['@concentration']))
    
#     # def __init__(self, xml):
#     #     self._xml = xml
#     #     self._bonds = Bonds()
#     #     self._label = None
#     #     self._compartment = None
#     #     self.molecules = []
#     #     # sets self.molecules up 
#     #     self._parse_xml(xml)

#     def add_item(self, item_tpl):
#         # TODO is this necessary? this should be defined in base
#         name, val = item_tpl
#         self._item_dict[name] = val

# class MoleculeTypes(ModelBlock):
#     '''
#     Molecule type block object that contains molecule types defined in the 
#     model. 

#     Item dictionary contains MolTypeXML object as the name has an empty 
#     string as the value thus outside of parsing this is basically 
#     the same as the base object.
#     '''
#     def __init__(self):
#         super().__init__()
#         self.name = "molecule types"

#     def __repr__(self):
#         return str(list(self._item_dict.keys()))

#     def add_item(self, item_tpl):
#         name, = item_tpl
#         self._item_dict[name] = ""
#         self._recompile = True

#     def __getitem__(self, key):
#         if isinstance(key, str):
#             # our keys are objects
#             for ikey in self._item_dict:
#                 if key == str(ikey):
#                     return self._item_dict[ikey]
#         if isinstance(key, int):
#             # get the item in order
#             return list(self._item_dict.keys())[key]
#         return self._item_dict[key]

#     def __setitem__(self, key, value):
#         for ikey in self._item_dict:
#             if key == str(ikey):
#                 self._recompile = True
#                 self._item_dict[ikey] = value

#     def __contains__(self, key):
#         for ikey in self._item_dict:
#             if key == str(ikey):
#                 return True
#         return False

#     def __str__(self):
#         # overwrites what the method returns when 
#         # it's converted to string
#         block_lines = ["\nbegin {}".format(self.name)]
#         for item in self._item_dict.keys():
#             block_lines.append("  " + "{}".format(item))
#         block_lines.append("end {}\n".format(self.name))
#         return "\n".join(block_lines)

#     def parse_xml_block(self, block_xml):
#         if isinstance(block_xml, list):
#             for md in block_xml:
#                 xmlobj = MolTypeXML(md)
#                 self.add_item((xmlobj,))
#         else:
#             xmlobj = MolTypeXML(block_xml)
#             self.add_item((xmlobj,))

# class Functions(ModelBlock):
#     '''
#     Function block object that contains functions defined in the 
#     model. 

#     Item dictionary contains the name of the function as the name
#     and function expression as value.
#     '''
#     def __init__(self):
#         super().__init__()
#         self.name = "functions"

#     # TODO: Fix this such that we can re-write functions
#     def __str__(self):
#         # overwrites what the method returns when 
#         # it's converted to string
#         block_lines = ["\nbegin {}".format(self.name)]
#         for item in self._item_dict.keys():
#             block_lines.append("  " + 
#                     "{} = {}".format(item, self._item_dict[item]))
#         block_lines.append("end {}\n".format(self.name))
#         return "\n".join(block_lines)

#     def parse_xml_block(self, block_xml):
#         if isinstance(block_xml, list):
#              for func in block_xml:
#                  xmlobj = FuncXML(func)
#                  self.add_item(xmlobj.item_tuple)
#         else:
#              xmlobj = FuncXML(block_xml)
#              self.add_item(xmlobj.item_tuple)

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

# class Actions(ModelBlock):
#     '''
#     Action block object that contains actions defined in the 
#     model. This is the one object that doesn't need a begin/end
#     block tag to be in the model. 

#     Item dictionary contains the action type as the name and a list
#     of arguments for that action as value. Each argument is of form 
#     [ArgumentName, ArgumentValue], method argument value is written
#     with quotes since that's the only one that needs quotes in BNGL.

#     Attributes
#     ----------
#     _action_list : list[str]
#         list of available action names
#     '''
#     def __init__(self):
#         super().__init__()
#         self.name = "actions"
#         self._action_list = ["generate_network", "generate_hybrid_model",
#             "simulate", "simulate_ode", "simulate_ssa", "simulate_pla", 
#             "simulate_nf", "parameter_scan", "bifurcate", "readFile", 
#             "writeFile", "writeModel", "writeNetwork", "writeXML", 
#             "writeSBML", "writeMfile", "writeMexfile", "writeMDL", 
#             "visualize", "setConcentration", "addConcentration", 
#             "saveConcentration", "resetConcentrations", "setParameter", 
#             "saveParameters", "resetParameters", "quit", "setModelName", 
#             "substanceUnits", "version", "setOption"]

#     def __str__(self):
#         # TODO: figure out every argument that has special 
#         # requirements, e.g. method requires the value to 
#         # be a string
#         block_lines = []
#         for item in self._item_dict.keys():
#             action_str = "{}(".format(item) + "{"
#             for iarg,arg in enumerate(self._item_dict[item]):
#                 val = arg[1]
#                 arg = arg[0]
#                 if iarg > 0:
#                     action_str += ","
#                 if arg == "method":
#                     action_str += '{}=>"{}"'.format(arg, val)
#                 else:
#                     action_str += '{}=>{}'.format(arg, val)
#             action_str += "})"
#             block_lines.append(action_str)
#         return "\n".join(block_lines)

#     def add_action(self, action_type, action_args):
#         '''
#         adds action, needs type as string and args as list of tuples
#         (which preserve order) of (argument, value) pairs
#         '''
#         if action_type in self._action_list:
#             self._item_dict[action_type] = action_args
#         else:
#             print("Action type {} not valid".format(action_type))

#     def clear_actions(self):
#         self._item_dict.clear()
# ###### MODEL STRUCTURES ###### 
