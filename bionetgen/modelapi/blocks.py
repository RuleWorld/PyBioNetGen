from .structs import Parameter, Compartment, Observable
from .structs import MoleculeType, Species, Function
from .structs import Rule, Action

# this import fails on some python versions
try:
    from typing import OrderedDict
except ImportError:
    from collections import OrderedDict

###### BLOCK OBJECTS ######
class ModelBlock:
    """
    Base block object that will be used for each block in the model.

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the begin {block} or end {block} statements, tuple
    items : OrderedDict
        all the model objects in the block
    _changes : OrderedDict
        a dictionary to keep track of all the changes done in a block
        after it is originally created
    _recompile : bool
        a tag that tells a potential future simulator if the model
        needs to be recompiled. TODO: has to be computed from _changes
        property upon get request.

    Methods
    -------
    reset_compilation_tags()
        resets _recompile and _changes tags for the block
    add_item((name,value))
        sets self.item[name] = value to add a particular model object
        into a block
    add_items(item_list)
        loops over every element in the list and uses add_item on it
    gen_string()
        for every block this method generates the BNGL string of the
        block. it has to be overwritten for each block.
    """

    def __init__(self) -> None:
        self.name = "ModelBlock"
        self.comment = (None, None)
        self._changes = OrderedDict()
        self._recompile = False
        self.items = OrderedDict()

    def __str__(self) -> str:
        return self.gen_string()

    def __len__(self) -> int:
        return len(self.items)

    def __repr__(self) -> str:
        # overwrites what the class representation
        # shows the items in the model block in
        # say ipython
        repr_str = "{} block with {} item(s): {}".format(
            self.name, len(self.items), list([i.name for i in self.items.values()])
        )
        return repr_str

    def __getitem__(self, key):
        if isinstance(key, int):
            # get the item in order
            return list(self.items.keys())[key]
        return self.items[key]

    def __setitem__(self, key, value) -> None:
        self.items[key] = value

    def __delitem__(self, key) -> None:
        if key in self.items:
            self.items.pop(key)
        else:
            print("Item {} not found".format(key))

    def __iter__(self):
        return self.items.keys().__iter__()

    def __contains__(self, key) -> bool:
        return key in self.items

    # TODO: Think extensively how this is going to work
    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items.keys():
                try:
                    new_value = float(value)
                    changed = True
                    self.items[name] = new_value
                except:
                    self.items[name] = value
                if changed:
                    self._changes[name] = new_value
                    self.__dict__[name] = new_value
        else:
            self.__dict__[name] = value

    def gen_string(self) -> str:
        # each block can have a comment at the start
        if self.comment[0] is not None:
            block_lines = ["\nbegin {} #{}".format(self.name, self.comment[0])]
        else:
            block_lines = ["\nbegin {}".format(self.name)]
        # now we just loop over lines
        for item in self.items.keys():
            block_lines.append(self.items[item].print_line())
        # each block can have a comment at the start
        if self.comment[1] is not None:
            block_lines.append("end {} #{}\n".format(self.name, self.comment[1]))
        else:
            block_lines.append("end {}\n".format(self.name))
        # join everything with new lines
        return "\n".join(block_lines)

    def reset_compilation_tags(self) -> None:
        # TODO: Make these properties such that it checks each
        # item for changes/recompile tags
        # for item in self.items:
        #     self.items[item]._recompile = False
        #     self.items[item]._changes = {}
        self._changes = OrderedDict()
        self._recompile = False

    def add_item(self, item_tpl) -> None:
        # TODO: try adding evaluation of the parameter here
        # for the future, in case we want people to be able
        # to adjust the math
        # TODO: Error handling, some names will definitely break this
        name, value = item_tpl
        # allow for empty addition, uses index
        if name is None:
            name = len(self.items)
        # set the line
        self.items[name] = value
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

    def add_items(self, item_list) -> None:
        for item in item_list:
            self.add_item(item)


class ParameterBlock(ModelBlock):
    """
    Parameter block object, subclass of ModelBlock.

    Methods
    -------
    add_parameter(name, value, expr=None)
        adds a parameter by making a new Parameter object and passing
        the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "parameters"

    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, Parameter):
                    # New parameter object
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    # A new expression
                    if self.items[name]["value"] != value:
                        changed = True
                        self.items[name]["value"] = value
                        self.items[name].write_expr = True
                else:
                    try:
                        # try a new value, we need to make sure
                        # to stop printing out the expression
                        value = float(value)
                        if self.items[name]["value"] != value:
                            changed = True
                            self.items[name]["value"] = value
                            self.items[name].write_expr = False
                    except:
                        print(
                            "can't set parameter {} to {}".format(
                                self.items[name]["name"], value
                            )
                        )
                if changed:
                    self._changes[name] = value
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def add_parameter(self, *args, **kwargs) -> None:
        p = Parameter(*args, **kwargs)
        self.add_item((p.name, p))


class CompartmentBlock(ModelBlock):
    """
    Compartment block object, subclass of ModelBlock.

    Methods
    -------
    add_compartment(name, dim, size, outside=None)
        adds a compartment by making a new Compartment object and passing
        the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "compartments"

    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, Compartment):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    try:
                        value = float(value)
                        if self.items[name]["size"] != value:
                            changed = True
                            self.items[name]["size"] = value
                    except:
                        print(
                            "can't set compartment {} to {}".format(
                                self.items[name]["name"], value
                            )
                        )
                if changed:
                    self._changes[name] = value
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def add_compartment(self, *args, **kwargs) -> None:
        c = Compartment(*args, **kwargs)
        self.add_item((c.name, c))


class ObservableBlock(ModelBlock):
    """
    Observable block object, subclass of ModelBlock.

    Methods
    -------
    add_observable(name, otype, patterns=[])
        adds an observable by making a new Observable object and passing
        the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "observables"

    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, Observable):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    print(
                        "can't set observable {} to {}".format(
                            self.items[name]["name"], value
                        )
                    )
                if changed:
                    self._changes[name] = value
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def add_observable(self, *args, **kwargs) -> None:
        o = Observable(*args, **kwargs)
        self.add_item((o.name, o))


class SpeciesBlock(ModelBlock):
    """
    Species block object, subclass of ModelBlock.

    Methods
    -------
    add_species(name, pattern=Pattern(), count=0)
        adds a species by making a new Species object and passing
        the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "species"

    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, Species):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    print(
                        "can't set species {} to {}".format(
                            self.items[name]["name"], value
                        )
                    )
                if changed:
                    self._changes[name] = value
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def add_species(self, *args, **kwargs) -> None:
        s = Species(*args, **kwargs)
        self.add_item((None, s))


class MoleculeTypeBlock(ModelBlock):
    """
    Molecule type block, subclass of ModelBlock.

    Methods
    -------
    add_molecule_type(name, name, components)
        adds a molecule type by making a new MoleculeType object and passing
        the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "molecule types"

    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, MoleculeType):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    print(
                        "can't set molecule type {} to {}".format(
                            self.items[name]["name"], value
                        )
                    )
                if changed:
                    self._changes[name] = value
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def add_molecule_type(self, name, components) -> None:
        mt = MoleculeType(name=name, components=components)
        self.add_item((name, mt))


class FunctionBlock(ModelBlock):
    """
    Function block object, subclass of ModelBlock.

    Methods
    -------
    add_function(name, name, expr, args=None)
        adds a function by making a new Function object and passing
        the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "functions"

    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, Function):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["expr"] != value:
                        changed = True
                        self.items[name]["expr"] = value
                else:
                    print(
                        "can't set function {} to {}".format(
                            self.items[name]["name"], value
                        )
                    )
                if changed:
                    self._changes[name] = value
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def add_function(self, *args, **kwargs) -> None:
        f = Function(*args, **kwargs)
        self.add_item((f.name, f))


class RuleBlock(ModelBlock):
    """
    Rule block object, subclass of ModelBlock.

    Methods
    -------
    add_rule(name, name, reactants=[], products=[], rate_constants=())
        adds a rule by making a new Rule object and passing
        the args/kwargs to its initialization.
    consolidate_rules : None
        XML loading makes it so that reversible rules are split
        into two unidirectional rules. This find them and combines
        them into a single rule to correctly represent the original
        model rule.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "reaction rules"

    def __setattr__(self, name, value) -> None:
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, Rule):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    print(
                        "can't set rule {} to {}".format(
                            self.items[name]["name"], value
                        )
                    )
                if changed:
                    self._changes[name] = value
                    self.__dict__[name] = value
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value

    def add_rule(self, *args, **kwargs) -> None:
        r = Rule(*args, **kwargs)
        self.add_item((r.name, r))

    def consolidate_rules(self) -> None:
        """
        Generated XML only has unidirectional rules
        and uses "_reverse_" tag to make bidirectional
        rules for NFSim. Take all the "_reverse_" tagged
        rules and convert them to bidirectional rules
        """
        delete_list = []
        for item_key in self.items:
            rxn_obj = self.items[item_key]
            if item_key.startswith("_reverse_"):
                # this is the reverse of another reaction
                reverse_of = item_key.replace("_reverse_", "")
                # ensure we have the original
                if reverse_of in self.items:
                    # make bidirectional and add rate law
                    r1 = self.items[reverse_of].rate_constants[0]
                    r2 = rxn_obj.rate_constants[0]
                    self.items[reverse_of].set_rate_constants((r1, r2))
                    # mark reverse for deletion
                    delete_list.append(item_key)
        # delete items marked for deletion
        for del_item in delete_list:
            self.items.pop(del_item)


class ActionBlock(ModelBlock):
    """
    Action block object, subclass of ModelBlock.This is the one object
    that doesn't need a begin/end block tag to be in the model.

    Attributes
    ----------
    _action_list : list[str]
        list of supported action names

    Methods
    -------
    add_action(name, action_type=None, action_args=[])
        adds an action by making a new Action object and passing
        the args/kwargs to its initialization.
    clear_actions()
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "actions"
        self._action_list = [
            "generate_network",
            "generate_hybrid_model",
            "simulate",
            "simulate_ode",
            "simulate_ssa",
            "simulate_pla",
            "simulate_nf",
            "parameter_scan",
            "bifurcate",
            "readFile",
            "writeFile",
            "writeModel",
            "writeNetwork",
            "writeXML",
            "writeSBML",
            "writeMfile",
            "writeMexfile",
            "writeMDL",
            "visualize",
            "setConcentration",
            "addConcentration",
            "saveConcentration",
            "resetConcentrations",
            "setParameter",
            "saveParameters",
            "resetParameters",
            "quit",
            "setModelName",
            "substanceUnits",
            "version",
            "setOption",
        ]

    def __setattr__(self, name, value) -> None:
        self.__dict__[name] = value

    def add_action(self, action_type, action_args) -> None:
        """
        adds action, needs type as string and args as list of tuples
        (which preserve order) of (argument, value) pairs
        """
        if action_type in self._action_list:
            a = Action(action_type=action_type, action_args=action_args)
            self.add_item((action_type, a))
        else:
            print("Action type {} not valid".format(action_type))

    def clear_actions(self) -> None:
        self.items.clear()

    def gen_string(self) -> str:
        block_lines = []
        # we just loop over lines for actions
        for item in self.items.keys():
            block_lines.append(self.items[item].print_line())
        # join everything with new lines
        return "\n".join(block_lines)
