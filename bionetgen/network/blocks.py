try:
    from typing import OrderedDict
except ImportError:
    from collections import OrderedDict
from bionetgen.core.utils.logging import BNGLogger
from .structs import NetworkParameter, NetworkCompartment, NetworkGroup
from .structs import NetworkSpecies, NetworkFunction, NetworkReaction
from .structs import NetworkEnergyPattern, NetworkPopulationMap

logger = BNGLogger()


###### BLOCK OBJECTS ######
class NetworkBlock:
    """
    Base block object that will be used for each block in the network.

    Attributes
    ----------
    name : str
        Name of the block which will be used to write the BNGL text
    comment : (str, str)
        comment at the begin {block} or end {block} statements, tuple
    items : OrderedDict
        all the model objects in the block

    Methods
    -------
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
        self.name = "NetworkBlock"
        self.comment = (None, None)
        self._changes = OrderedDict()
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
            except Exception as exc:
                logger.warning(
                    f"Unable to bind attribute {name!r} for the {self.name} block;"
                    " the item remains available via block.items. "
                    f"Original error: {exc}",
                    loc=f"{__file__} : NetworkBlock.add_item()",
                )
        # we just added an item to a block, let's assume we need
        # to recompile if we have a compiled simulator
        self._recompile = True

    def add_items(self, item_list) -> None:
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
                    f" {value!r}; keeping existing {num_field}"
                    f" {self.items[name][num_field]!r}",
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


class NetworkParameterBlock(NetworkBlock):
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
            item_cls=NetworkParameter,
            str_field="value",
            num_field="value",
            write_expr_field="write_expr",
            kind="parameter",
        )

    def add_parameter(self, *args, **kwargs) -> None:
        p = NetworkParameter(*args, **kwargs)
        self.add_item((p.name, p))


class NetworkCompartmentBlock(NetworkBlock):
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
            item_cls=NetworkCompartment,
            str_field="name",
            num_field="size",
            kind="compartment",
        )

    def add_compartment(self, *args, **kwargs) -> None:
        c = NetworkCompartment(*args, **kwargs)
        self.add_item((c.name, c))


class NetworkGroupBlock(NetworkBlock):
    """
    Group block object, subclass of NetworkBlock.

    Methods
    -------
    add_group(name, otype, patterns=[])
        adds an group by making a new NetworkGroup object and passing
        the args/kwargs to its initialization.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "groups"

    def __setattr__(self, name, value) -> None:
        self._set_item_attribute(
            name,
            value,
            item_cls=NetworkGroup,
            str_field="name",
            kind="group",
        )

    def add_group(self, *args, **kwargs) -> None:
        g = NetworkGroup(*args, **kwargs)
        self.add_item((g.name, g))


class NetworkSpeciesBlock(NetworkBlock):
    """
    Species block object, subclass of NetworkBlock.

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
            item_cls=NetworkSpecies,
            str_field="name",
            kind="species",
        )

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value) -> None:
        self.items[key] = value

    def add_species(self, *args, **kwargs) -> None:
        s = NetworkSpecies(*args, **kwargs)
        ctr = len(self.items)
        self.add_item((ctr, s))


class NetworkFunctionBlock(NetworkBlock):
    """
    Function block object, subclass of NetworkBlock.

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
            item_cls=NetworkFunction,
            str_field="expr",
            kind="function",
        )

    def add_function(self, *args, **kwargs) -> None:
        f = NetworkFunction(*args, **kwargs)
        self.add_item((f.name, f))


class NetworkReactionBlock(NetworkBlock):
    """
    Rule block object, subclass of NetworkBlock.

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
        self.name = "reactions"

    def __setattr__(self, name, value) -> None:
        self._set_item_attribute(
            name,
            value,
            item_cls=NetworkReaction,
            str_field="name",
            kind="reaction",
        )

    def add_reaction(self, *args, **kwargs) -> None:
        r = NetworkReaction(*args, **kwargs)
        self.add_item((r.name, r))


class NetworkEnergyPatternBlock(NetworkBlock):
    """
    Energy pattern block object, subclass of NetworkBlock.

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
            item_cls=NetworkEnergyPattern,
            str_field="name",
            kind="energy pattern",
        )

    def add_energy_pattern(self, *args, **kwargs) -> None:
        ep = NetworkEnergyPattern(*args, **kwargs)
        self.add_item((ep.name, ep))


class NetworkPopulationMapBlock(NetworkBlock):
    """
    Population map block object, subclass of NetworkBlock.

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
            item_cls=NetworkPopulationMap,
            str_field="name",
            kind="population map",
        )

    def add_population_map(self, *args, **kwargs) -> None:
        pm = NetworkPopulationMap(*args, **kwargs)
        self.add_item((pm.name, pm))
