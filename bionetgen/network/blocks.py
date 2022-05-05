try:
    from typing import OrderedDict
except ImportError:
    from collections import OrderedDict
from .structs import NetworkParameter, NetworkCompartment, NetworkGroup
from .structs import NetworkSpecies, NetworkFunction, NetworkReaction
from .structs import NetworkEnergyPattern, NetworkPopulationMap

# this import fails on some python versions
try:
    from typing import OrderedDict
except ImportError:
    from collections import OrderedDict

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
                # print("can't set {} to {}".format(name, value))
                pass
        # we just added an item to a block, let's assume we need
        # to recompile if we have a compiled simulator
        self._recompile = True

    def add_items(self, item_list) -> None:
        for item in item_list:
            self.add_item(item)


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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkParameter):
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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkCompartment):
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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkGroup):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    print(
                        "can't set group {} to {}".format(
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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkSpecies):
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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkFunction):
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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkReaction):
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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkEnergyPattern):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    print(
                        "can't set energy pattern {} to {}".format(
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
        changed = False
        if hasattr(self, "items"):
            if name in self.items:
                if isinstance(value, NetworkPopulationMap):
                    changed = True
                    self.items[name] = value
                elif isinstance(value, str):
                    if self.items[name]["name"] != value:
                        changed = True
                        self.items[name]["name"] = value
                else:
                    print(
                        "can't set population map {} to {}".format(
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

    def add_population_map(self, *args, **kwargs) -> None:
        pm = NetworkPopulationMap(*args, **kwargs)
        self.add_item((pm.name, pm))
