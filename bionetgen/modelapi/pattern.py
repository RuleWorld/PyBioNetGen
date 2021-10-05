# All classes that deal with patterns
class Pattern:
    """
    Pattern object. Fundamentally it's just a list of molecules
    which are defined later.

    Attributes
    ----------
    _bonds : Bonds
        setting a pattern requires you to keep track of all bonds to
        correctly label them, this object tracks everything
    _compartment : str
        compartment of the overall pattern (not the same thing as
        molecule compartment, those have their own)
    _label : str
        label of the overall pattern (not the same thing as molecule
        label, those have their own)
    molecules : list[Molecule]
        list of molecule objects that are in the pattern
    fixed : bool
        used for constant species, sets "$" at the beginning of the
        pattern string
    MatchOnce : bool
        used for matchOnce syntax, "{MatchOnce}PatternStr"
    """

    def __init__(self, molecules=[], bonds=None, compartment=None, label=None):
        self.molecules = molecules
        self._bonds = bonds
        self._compartment = compartment
        self._label = label
        self.fixed = False
        self.MatchOnce = False

    @property
    def compartment(self):
        return self._compartment

    @compartment.setter
    def compartment(self, value):
        # TODO: Build in logic to set the
        # outer compartment
        # print("Warning: Logical checks are not complete")
        self._compartment = value
        # by default, once the outer compartment is set
        # we will set the compartment of each molecule
        # to that new compartment.
        for molec in self.molecules:
            molec.compartment = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        # TODO: Build in logic to set
        # the outer label
        # print("Warning: Logical checks are not complete")
        self._label = value

    def __str__(self):
        sstr = ""
        if self.fixed:
            sstr += "$"
        if self.MatchOnce:
            sstr += "{MatchOnce}"
        for imol, mol in enumerate(self.molecules):
            if imol == 0 and self.compartment is not None:
                sstr += "@{}:".format(self.compartment)
            if imol == 0 and self.label is not None:
                sstr += "%{}:".format(self.label)
            if imol > 0:
                sstr += "."
            sstr += str(mol)
        return sstr

    def __repr__(self):
        return str(self)

    def __getitem__(self, key):
        return self.molecules[key]

    def __iter__(self):
        return self.molecules.__iter__()

    # TODO: Implement __contains__


class Molecule:
    """
    Molecule object. A pattern is a list of molecules.
    This object also handles molecule types where components
    have a list of possible states.

    Attributes
    ----------
    _name : str
        name of the molecule
    _compartment : str
        compartment of the molecule
    _label : str
        label of the molecule
    _components : list[Component]
        list of components for this molecule

    Methods
    -------
    add_component(name, state=None, states=[])
        add a component object to the list of components with name
        "name", current state "state" or a list of states
        (for molecule types) "states"
    """

    def __init__(self, name="0", components=[], compartment=None, label=None):
        self._name = name
        self._components = components
        self._compartment = compartment
        self._label = label

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.components[key]

    def __iter__(self):
        return self.components.__iter__()

    # TODO: implement __setitem__,  __contains__

    def __str__(self):
        mol_str = self.name
        if self.label is not None:
            mol_str += "%{}".format(self.label)
        mol_str += "("
        if len(self.components) > 0:
            for icomp, comp in enumerate(self.components):
                if icomp > 0:
                    mol_str += ","
                mol_str += str(comp)
        mol_str += ")"
        if self.compartment is not None:
            mol_str += "@{}".format(self.compartment)
        return mol_str

    ### PROPERTIES ###
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        # print("Warning: Logical checks are not complete")
        # TODO: Check for invalid characters
        self._name = value

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, value):
        # print("Warning: Logical checks are not complete")
        self._components = value

    def __repr__(self):
        return str(self)

    @property
    def compartment(self):
        return self._compartment

    @compartment.setter
    def compartment(self, value):
        # print("Warning: Logical checks are not complete")
        self._compartment = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        # print("Warning: Logical checks are not complete")
        self._label = value

    def _add_component(self, name, state=None, states=[]):
        comp_obj = Component()
        comp_obj.name = name
        comp_obj.state = state
        comp_obj.states = states
        self.components.append(comp_obj)

    def add_component(self, name, state=None, states=[]):
        # TODO: Add built-in logic here
        # print("Warning: Logical checks are not complete")
        self._add_component(name, state, states)


class Component:
    """
    Component object that describes the state, label and bonding
    for each component. Molecules can optionally contain components

    Attributes
    ----------
    name : str
        name of the component
    _label : str
        label of the component
    _state : str
        state of the component, not used for molecule types
    _states : list[str]
        list of states for molecule types
    _bonds : list[Bond]
        list of bond objects that describes bonding of the component

    Methods
    -------
    add_state()
        not implemented. will eventually be used to add additional states
        to an existing component
    add_bond()
        not implemented. will eventually be used to add additional bonds
        to an existing component
    """

    def __init__(self):
        self._name = ""
        self._label = None
        self._state = None
        self._states = []
        self._bonds = []

    def __repr__(self):
        return str(self)

    def __str__(self):
        comp_str = self.name
        # only for molecule types
        if len(self.states) > 0:
            for istate, state in enumerate(self.states):
                comp_str += "~{}".format(state)
        # for any other pattern
        if self.state is not None:
            comp_str += "~{}".format(self.state)
        if self.label is not None:
            comp_str += "%{}".format(self.label)
        if len(self.bonds) > 0:
            for bond in self.bonds:
                comp_str += "!{}".format(bond)
        return comp_str

    ### PROPERTIES ###
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        # TODO: Add built-in logic here
        # print("Warning: Logical checks are not complete")
        self._name = value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        # TODO: Add built-in logic here
        # print("Warning: Logical checks are not complete")
        self._label = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        # TODO: Add built-in logic here
        # print("Warning: Logical checks are not complete")
        self._state = value

    @property
    def states(self):
        return self._states

    @states.setter
    def states(self, value):
        # TODO: Add built-in logic here
        # print("Warning: Logical checks are not complete")
        self._states = value

    @property
    def bonds(self):
        return self._bonds

    @bonds.setter
    def bonds(self, value):
        # TODO: Add built-in logic here
        # print("Warning: Logical checks are not complete")
        self._bonds = value

    def _add_state(self):
        raise NotImplementedError

    def add_state(self):
        self._add_state()

    def _add_bond(self):
        raise NotImplementedError

    def add_bond(self):
        self._add_bond()
