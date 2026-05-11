try:
    from typing import OrderedDict
except ImportError:
    from collections import OrderedDict
from bionetgen.core.utils.logging import BNGLogger
from bionetgen.core.utils.utils import ActionList
from .structs import Parameter, Compartment, Observable
from .structs import MoleculeType, Species, Function
from .structs import Rule, Action
from .structs import EnergyPattern, PopulationMap

logger = BNGLogger()


###### BLOCK OBJECTS ######
class ModelBlock:
    """
    Base block object that will be used for each block in the model.

    These objects will implement the following python internal functions
    to make them feel more natural in a python environment:
        __str__, __repr__, __len__, __getitem__, __setitem__,
        __delitem__, __iter__, __contains__

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
        self.items.pop(key)

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
                except (TypeError, ValueError):
                    self.items[name] = value
                else:
                    changed = True
                    self.items[name] = new_value
                if changed:
                    self._changes[name] = new_value
                    self.__dict__[name] = new_value
        else:
            self.__dict__[name] = value

    def gen_string(self) -> str:
        """
        Generates the string for the block from the object.
        """
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
        """
        Resets the change history for this block.
        """
        # TODO: Make these properties such that it checks each
        # item for changes/recompile tags
        # for item in self.items:
        #     self.items[item]._recompile = False
        #     self.items[item]._changes = {}
        self._changes = OrderedDict()
        self._recompile = False

    def add_item(self, item_tpl) -> None:
        """
        Adds an item to the block from the item tuple given.
        Exact mechanism is slightly different for each block.
        """
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
            except Exception as exc:
                logger.warning(
                    f"Unable to bind attribute {name!r} for the {self.name} block;"
                    " the item remains available via block.items. "
                    f"Original error: {exc}",
                    loc=f"{__file__} : ModelBlock.add_item()",
                )
        # we just added an item to a block, let's assume we need
        # to recompile if we have a compiled simulator
        self._recompile = True

    def add_items(self, item_list) -> None:
        """
        Calls `add_item` for each tuple for a list of tuples.
        """
        for item in item_list:
            self.add_item(item)

    def _set_item_attribute(
        self,
        name,
        value,
        *,
        item_cls,
        str_field,
        kind,
        num_field=None,
        write_expr_field=None,
    ) -> None:
        """Shared `__setattr__` path for blocks that hold named items."""
        if not hasattr(self, "items"):
            self.__dict__[name] = value
            return
        if name not in self.items:
            self.__dict__[name] = value
            return
        changed = False
        if isinstance(value, item_cls):
            changed = True
            self.items[name] = value
        elif isinstance(value, str):
            if self.items[name][str_field] != value:
                changed = True
                self.items[name][str_field] = value
                if write_expr_field is not None:
                    setattr(self.items[name], write_expr_field, True)
        elif num_field is not None:
            try:
                new_value = float(value)
            except (TypeError, ValueError):
                logger.warning(
                    f"Unable to set {kind} {self.items[name]['name']!r} to"
                    f" {value!r}; keeping existing {kind}",
                    loc=f"{__file__} : {self.__class__.__name__}.__setattr__()",
                )
            else:
                if self.items[name][num_field] != new_value:
                    changed = True
                    self.items[name][num_field] = new_value
                    if write_expr_field is not None:
                        setattr(self.items[name], write_expr_field, False)
                    value = new_value
        else:
            logger.warning(
                f"Unable to set {kind} {self.items[name]['name']!r} to"
                f" {value!r}; keeping existing {kind}",
                loc=f"{__file__} : {self.__class__.__name__}.__setattr__()",
            )
        if changed:
            self._changes[name] = value
            self.__dict__[name] = value


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
        self._set_item_attribute(
            name,
            value,
            item_cls=Parameter,
            str_field="value",
            num_field="value",
            write_expr_field="write_expr",
            kind="parameter",
        )

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
        self._set_item_attribute(
            name,
            value,
            item_cls=Compartment,
            str_field="name",
            num_field="size",
            kind="compartment",
        )

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
        self._set_item_attribute(
            name,
            value,
            item_cls=Observable,
            str_field="name",
            kind="observable",
        )

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
        self._set_item_attribute(
            name,
            value,
            item_cls=Species,
            str_field="name",
            kind="species",
        )

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value) -> None:
        self.items[key] = value

    def add_species(self, *args, **kwargs) -> None:
        s = Species(*args, **kwargs)
        ctr = len(self.items)
        self.add_item((ctr, s))


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
        self._set_item_attribute(
            name,
            value,
            item_cls=MoleculeType,
            str_field="name",
            kind="molecule type",
        )

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
        self._set_item_attribute(
            name,
            value,
            item_cls=Function,
            str_field="expr",
            kind="function",
        )

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
        self._set_item_attribute(
            name,
            value,
            item_cls=Rule,
            str_field="name",
            kind="rule",
        )

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
                    if r1.startswith("Arrhenius"):
                        self.items[reverse_of].set_rate_constants([r1])
                    else:
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
    add_action(name, action_type=None, action_args={})
        adds an action by making a new Action object and passing
        the args/kwargs to its initialization.
    clear_actions()
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "actions"
        self.AList = ActionList()
        self._action_list = self.AList.possible_types
        self.items = []
        self.before_model = []

    def __setattr__(self, name, value) -> None:
        self.__dict__[name] = value

    def add_item(self, item_tpl) -> None:
        name, value = item_tpl
        # check to see if it's a before model action
        if self.AList.is_before_model(name):
            self.before_model.append(value)
        else:
            # set the line
            self.items.append(value)

    def __repr__(self) -> str:
        # overwrites what the class representation
        # shows the items in the model block in
        # say ipython
        repr_str = "{} block with {} item(s): {}".format(
            self.name, len(self.items), self.items
        )
        return repr_str

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value) -> None:
        self.items[key] = value

    def __delitem__(self, key) -> None:
        return self.items.pop(key)

    def __iter__(self):
        return range(len(self.items)).__iter__()

    def __contains__(self, key) -> bool:
        return (key in self.items) or (key in [x.name for x in self.items])

    def add_action(self, action_type, action_args) -> None:
        """
        adds action, needs type as string and args as list of tuples
        (which preserve order) of (argument, value) pairs
        """
        a = Action(action_type=action_type, action_args=action_args)
        self.add_item((action_type, a))

    def clear_actions(self) -> None:
        self.items.clear()

    def gen_string(self) -> str:
        block_lines = []
        # we just loop over lines for actions
        for item in self.items:
            block_lines.append(item.print_line())
        # join everything with new lines
        return "\n".join(block_lines)


class ProtocolBlock(ActionBlock):
    """
    Protocol block object, subclass of ActionBlock.

    Protocol lines live inside ``begin model``/``end model`` and must
    retain their own begin/end block wrapper rather than being rendered
    as top-level actions.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "protocol"

    def add_item(self, item_tpl) -> None:
        _, value = item_tpl
        self.items.append(value)

    def gen_string(self) -> str:
        block_lines = ["\nbegin protocol"]
        block_lines.extend(item.print_line() for item in self.items)
        block_lines.append("end protocol\n")
        return "\n".join(block_lines)


class EnergyPatternBlock(ModelBlock):
    """
    Energy pattern block object, subclass of ModelBlock.

    Methods
    -------
    add_energy_pattern(id, pattern, expression)
        adds an energy pattern by making a new EnergyPattern object
        and passing the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "energy patterns"

    def __setattr__(self, name, value) -> None:
        self._set_item_attribute(
            name,
            value,
            item_cls=EnergyPattern,
            str_field="name",
            kind="energy pattern",
        )

    def add_energy_pattern(self, *args, **kwargs) -> None:
        ep = EnergyPattern(*args, **kwargs)
        self.add_item((ep.name, ep))


class PopulationMapBlock(ModelBlock):
    """
    Population map block object, subclass of ModelBlock.

    Methods
    -------
    add_population_map(id, struct_species, pop_species, rate)
        adds a population map by making a new PopulationMap object
        and passing the args/kwargs to its initialization
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "population maps"

    def __setattr__(self, name, value) -> None:
        self._set_item_attribute(
            name,
            value,
            item_cls=PopulationMap,
            str_field="name",
            kind="population map",
        )

    def add_population_map(self, *args, **kwargs) -> None:
        pm = PopulationMap(*args, **kwargs)
        self.add_item((pm.name, pm))
