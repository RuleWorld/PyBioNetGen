from typing import OrderedDict
from .lines import ParameterLine, CompartmentLine, ObservableLine
from .lines import SpeciesLine, MolTypeLine, FunctionLine
from .lines import RuleLine, ActionLine
###### BLOCK OBJECTS ###### 
class ModelBlock:
    '''
    Base block object that will be used for each block in BNGL.

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block


    Methods
    -------
    reset_compilation_tags()
        resets _recompile and _changes tag for the block
    add_item(item_tpl)
        while every block can implement their own add_item method
        the base assumption that each element has a name and value
        so this method takes in (name,value) tuple and sets 
        _item_dict[name] = value
    add_items(item_list)
        loops over every element in the list and uses add_item on it
    '''
    def __init__(self):
        self.name = "ModelBlock"
        self.lines = OrderedDict()
        self.comment = (None, None)

    def __str__(self):
        # each block can have a comment at the start
        if self.comment[0] is not None:
            block_lines = ["\nbegin {} #{}".format(self.name, self.comment[0])]
        else:
            block_lines = ["\nbegin {}".format(self.name)]
        # now we just loop over lines
        for line in self.lines.keys():
            block_lines.append(str(self.lines[line]))
        # each block can have a comment at the start
        if self.comment[1] is not None:
            block_lines.append("end {} #{}\n".format(self.name, self.comment[1]))
        else :
            block_lines.append("end {}\n".format(self.name))
        # join everything with new lines
        return "\n".join(block_lines)

    def __len__(self):
        return len(self.lines)

    def __repr__(self):
        # overwrites what the class representation
        # shows the items in the model block in 
        # say ipython
        return str(self.lines)

    def __getitem__(self, key):
        if isinstance(key, int):
            # get the item in order
            return list(self.lines.keys())[key]
        return self.lines[key]

    def __setitem__(self, key, value):
        self.lines[key] = value

    def __delitem__(self, key):
        if key in self.lines:
            self.lines.pop(key)
        else: 
            print("Item {} not found".format(key))

    def __iter__(self):
        return self.lines.keys().__iter__()

    def __contains__(self, key):
        return key in self.lines
    
    def reset_compilation_tags(self):
        # TODO: Make these properties such that it checks each 
        # line for changes/recompile tags
        for line in self.lines:
            line._recompile = False
            line._changes = {}
    
    def add_item(self, item_tpl):
        # TODO: try adding evaluation of the parameter here
        # for the future, in case we want people to be able
        # to adjust the math
        # TODO: Error handling, some names will definitely break this
        name, value = item_tpl
        # allow for empty addition, uses index
        if name is None:
            name = len(self.lines)
        # set the line
        self.lines[name] = value
        # if the name is a string, try adding as an attribute
        if isinstance(name, str):
            try:
                setattr(self, name, value)
            except:
                print("can't set {} to {}".format(name, value))
                pass
        # we just added an item to a block, let's assume we need 
        # to recompile if we have a compiled simulator
        self._recompile = True

    def add_items(self, item_list):
        for item in item_list:
            self.add_item(item)
    
    # TODO: Think extensively how this is going to work
    # def __setattr__(self, name, value):
    #     changed = False
    #     if hasattr(self, "_item_dict"):
    #         if name in self._item_dict.keys():
    #             try: 
    #                 new_value = float(value)
    #                 changed = True
    #                 self._item_dict[name] = new_value
    #             except:
    #                 self._item_dict[name] = value
    #     if changed:
    #         self._changes[name] = new_value
    #         self.__dict__[name] = new_value
    #     else:
    #         self.__dict__[name] = value


class ParameterBlock(ModelBlock):
    '''
    Parameter block object.

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block
    '''
    def __init__(self):
        super().__init__()
        self.name = "parameters"

    # def add_parameter(self):
    #     pass


class CompartmentBlock(ModelBlock):
    '''
    Compartment block object. 

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block
    '''
    def __init__(self):
        super().__init__()
        self.name = "compartments"


class ObservableBlock(ModelBlock):
    '''
    Observable block object.  

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block
    '''
    def __init__(self):
        super().__init__()
        self.name = "observables"


class SpeciesBlock(ModelBlock):
    '''
    Species block object.

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block
    '''
    def __init__(self):
        super().__init__()
        self.name = "species"


class MoleculeTypes(ModelBlock):
    '''
    Molecule type block. 

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block
    '''
    def __init__(self):
        super().__init__()
        self.name = "molecule types"


class FunctionBlock(ModelBlock):
    '''
    Function block object. 

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block
    '''
    def __init__(self):
        super().__init__()
        self.name = "functions"


class RuleBlock(ModelBlock):
    '''
    Rule block object. 

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the beginning or the end
    lines : OrderedDict
        Ordered dictionary of line objects in each block

    Methods
    -------
    consolidate_rules : None
        TODO
    '''
    def __init__(self):
        super().__init__()
        self.name = "reaction rules"

    def consolidate_rules(self) -> None:
        '''
        Generated XML only has unidirectional rules
        and uses "_reverse_" tag to make bidirectional 
        rules for NFSim. Take all the "_reverse_" tagged
        rules and convert them to bidirectional rules
        '''
        delete_list = []
        for item_key in self._item_dict:
            rxn_obj  = self._item_dict[item_key]
            if item_key.startswith("_reverse_"):
                # this is the reverse of another reaction
                reverse_of = item_key.replace("_reverse_", "")
                # ensure we have the original
                if reverse_of in self._item_dict:
                    # make bidirectional and add rate law
                    r1 = self._item_dict[reverse_of].rate_constants[0]
                    r2 = rxn_obj.rate_constants[0]
                    self._item_dict[reverse_of].set_rate_constants((r1,r2))
                    # mark reverse for deletion
                    delete_list.append(item_key)
        # delete items marked for deletion
        for del_item in delete_list:
            self._item_dict.pop(del_item)


class ActionBlock(ModelBlock):
    '''
    Action block object that contains actions defined in the 
    model. This is the one object that doesn't need a begin/end
    block tag to be in the model. 

    Item dictionary contains the action type as the name and a list
    of arguments for that action as value. Each argument is of form 
    [ArgumentName, ArgumentValue], method argument value is written
    with quotes since that's the only one that needs quotes in BNGL.

    Attributes
    ----------
    _action_list : list[str]
        list of available action names
    '''
    def __init__(self):
        super().__init__()
        self.name = "actions"
        self._action_list = ["generate_network", "generate_hybrid_model",
            "simulate", "simulate_ode", "simulate_ssa", "simulate_pla", 
            "simulate_nf", "parameter_scan", "bifurcate", "readFile", 
            "writeFile", "writeModel", "writeNetwork", "writeXML", 
            "writeSBML", "writeMfile", "writeMexfile", "writeMDL", 
            "visualize", "setConcentration", "addConcentration", 
            "saveConcentration", "resetConcentrations", "setParameter", 
            "saveParameters", "resetParameters", "quit", "setModelName", 
            "substanceUnits", "version", "setOption"]

    def add_action(self, action_type, action_args):
        '''
        adds action, needs type as string and args as list of tuples
        (which preserve order) of (argument, value) pairs
        '''
        if action_type in self._action_list:
            self._item_dict[action_type] = action_args
        else:
            print("Action type {} not valid".format(action_type))

    def clear_actions(self):
        self._item_dict.clear()
