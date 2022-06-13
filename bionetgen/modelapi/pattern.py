from bionetgen.core.utils.logging import BNGLogger

logger = BNGLogger()

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
    compartment : str
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

    def __init__(
        self, molecules=[], bonds=None, compartment=None, label=None, canonicalize=False
    ):
        self.molecules = molecules
        self._bonds = bonds
        self.compartment = compartment
        self.label = label
        self.fixed = False
        self.MatchOnce = False
        self.relation = None
        self.quantity = None
        self.nautyG = None
        self.canonical_certificate = None
        self.canonical_label = None
        if canonicalize:
            self.canonicalize()

    def canonicalize(self):
        # set a location for logging
        loc = f"{__file__} : Pattern.canonicalize()"
        # try importing pynauty to canonicalize the labeling
        try:
            import pynauty
        except ImportError:
            logger.warning(
                f"Importing pynauty failed, cannot canonicalize. Pattern equality checking is not guaranteed to work for highly symmetrical species.",
                loc=loc,
            )
            return
        # find how many vertices we need
        lmol = len(self.molecules)
        lcomp = sum([len(x.components) for x in self.molecules])
        node_cnt = lmol + lcomp
        # initialize our pynauty graph
        G = pynauty.Graph(node_cnt)
        # going to need to figure out bonding
        bond_dict = {}
        # save our IDs
        rev_grpIds = {}
        grpIds = {}
        # also pointers to each object
        node_ptrs = {}
        bond_node_ptrs = {}
        # we'll need to seutp coloring
        colors = {}
        currId = 0
        mCopyId = 0
        cCopyId = 0
        # let's loop over everything in the pattern
        for molec in self.molecules:
            # setting colors
            color_id = (molec.name, None, None)
            if color_id in colors:
                colors[color_id].add(currId)
            else:
                colors[color_id] = set([currId])
            # saving IDs
            parent_id = (molec.name, None, mCopyId, cCopyId)
            if parent_id in grpIds:
                mCopyId += 1
                parent_id = (molec.name, None, mCopyId, cCopyId)
                grpIds[parent_id] = currId
            else:
                grpIds[parent_id] = currId
            rev_grpIds[currId] = parent_id
            node_ptrs[currId] = molec
            currId += 1
            # now looping over components
            for comp in molec.components:
                # saving component coloring
                comp_color_id = (molec.name, comp.name, comp.state)
                if comp_color_id in colors:
                    colors[comp_color_id].add(currId)
                else:
                    colors[comp_color_id] = set([currId])
                chid_id = (molec.name, comp.name, mCopyId, cCopyId)
                # connecting the component to the molecule
                G.connect_vertex(grpIds[parent_id], [currId])
                # saving component IDs
                if chid_id in grpIds:
                    cCopyId += 1
                    chid_id = (molec.name, comp.name, mCopyId, cCopyId)
                    grpIds[chid_id] = currId
                else:
                    grpIds[chid_id] = currId
                rev_grpIds[currId] = chid_id
                node_ptrs[currId] = comp
                currId += 1
                # saving bonds
                if len(comp._bonds) != 0:
                    for bond in comp._bonds:
                        if bond not in bond_dict.keys():
                            bond_dict[bond] = [chid_id]
                        else:
                            bond_dict[bond].append(chid_id)
        # now we got everything, we implement it in the graph
        for bond in bond_dict:
            # check if each of our bonds have exactly two end points
            if len(bond_dict[bond]) == 2:
                id1 = bond_dict[bond][0]
                id1 = grpIds[id1]
                id2 = bond_dict[bond][1]
                id2 = grpIds[id2]
                G.connect_vertex(id1, [id2])
            else:
                # raise a warning
                logger.warning(
                    f"Bond {bond} doesn't have exactly 2 end points, please check that you don't have any dangling bonds.",
                    loc=loc,
                )
        # we get our color sets
        color_sets = list(colors.values())
        # set vertex coloring
        G.set_vertex_coloring(color_sets)
        # save our graph
        self.nautyG = G
        # generate the canonical certificate for the entire graph
        self.canonical_certificate = pynauty.certificate(self.nautyG)
        # generate the canonical label for the entire graph
        # first, we give every node their canonical order
        canon_order = pynauty.canon_label(self.nautyG)
        for iordr, ordr in enumerate(canon_order):
            node_ptrs[ordr].canonical_order = iordr
        # relabeling bonds
        relabeling_bond_dict = {}
        for bond in bond_dict:
            # check if each of our bonds have exactly two end points
            if len(bond_dict[bond]) == 2:
                id1 = bond_dict[bond][0]
                id1 = grpIds[id1]
                comp1 = node_ptrs[id1]
                id2 = bond_dict[bond][1]
                id2 = grpIds[id2]
                comp2 = node_ptrs[id2]
                parent_order = min(
                    comp1.parent_molecule.canonical_order,
                    comp2.parent_molecule.canonical_order,
                )
                comp_order = min(comp1.canonical_order, comp2.canonical_order)
                relabeling_bond_dict[(parent_order, comp_order)] = (comp1, comp2)
            else:
                # raise a warning
                logger.warning(
                    f"Bond {bond} doesn't have exactly 2 end points, please check that you don't have any dangling bonds.",
                    loc=loc,
                )
        # this will give us the keys to canonically sorted bonds
        sorted_order = sorted(relabeling_bond_dict.keys())
        for ibond, sbond in enumerate(sorted_order):
            # now we add a canonical bond ID to each component
            c1, c2 = relabeling_bond_dict[sbond]
            if c1.canonical_bonds is None:
                c1.canonical_bonds = [str(ibond + 1)]
            else:
                c1.canonical_bonds.append(str(ibond + 1))
            if c2.canonical_bonds is None:
                c2.canonical_bonds = [str(ibond + 1)]
            else:
                c2.canonical_bonds.append(str(ibond + 1))
        # and now we can get the canonical label
        self.canonical_label = self.print_canonical()

    def print_canonical(self):
        # need to make sure we don't print useless compartments
        self.consolidate_molecule_compartments()
        canon_label = ""
        # we first deal with the pattern compartment
        if self.compartment is not None:
            canon_label += "@{}".format(self.compartment)
        if self.label is not None:
            canon_label += "%{}".format(self.label)
        if self.label is not None or self.compartment is not None:
            canon_label += ":"
        # now loop over all molecules in canonical order
        canon_ords = [m.canonical_order for m in self.molecules]
        canon_ord_pairs = zip(range(len(self.molecules)), canon_ords)
        sorted_canon_ord_pairs = sorted(canon_ord_pairs, key=lambda x: x[1])
        for imol, mol in enumerate(sorted_canon_ord_pairs):
            mol_id = mol[0]
            if imol == 0:
                if self.fixed:
                    canon_label += "$"
                if self.MatchOnce:
                    canon_label += "{MatchOnce}"
            if imol > 0:
                canon_label += "."
            canon_label += self.molecules[mol_id].print_canonical()
        if self.relation is not None:
            canon_label += f"{self.relation}{self.quantity}"
        return canon_label

    def __contains__(self, val):
        return val in self.molecules

    def __eq__(self, other):
        loc = f"{__file__} : Pattern.__eq__()"
        if isinstance(other, Pattern):
            logger.debug(f"Comparison class matches: {other.__class__}", loc=loc)
            # checking pattern-wide properties
            if (other.compartment == self.compartment) and (other.label == self.label):
                logger.debug(
                    f"Compartment or label matches: {other.compartment}, {other.label}",
                    loc=loc,
                )
                # checking mods
                if (other.fixed == self.fixed) and (other.MatchOnce == self.MatchOnce):
                    logger.debug(
                        f"fixed or matchonce matches: {other.fixed}, {other.MatchOnce}",
                        loc=loc,
                    )
                    # checking quantifiers
                    if (other.relation == self.relation) and (
                        other.quantity == self.quantity
                    ):
                        logger.debug(
                            f"relation or quantity matches: {other.relation}, {other.quantity}",
                            loc=loc,
                        )
                        # if we made the label, we can just compare the two
                        if (self.canonical_label is not None) and (
                            other.canonical_label is not None
                        ):
                            return self.canonical_label == other.canonical_label
                        # now we can check contents
                        for molecule in self:
                            if molecule not in other.molecules:
                                logger.debug(
                                    f"molecule doesn't match: {molecule}", loc=loc
                                )
                                return False
                        # isomorphism check if we have the certificate
                        if (self.canonical_certificate is not None) and (
                            other.canonical_certificate is not None
                        ):
                            if (
                                self.canonical_certificate
                                != other.canonical_certificate
                            ):
                                return False
                        # TODO: molecules match, check bonds
                        # Bonds match, patterns are the same
                        logger.debug("patterns match!", loc=loc)
                        return True
        return False

    @property
    def compartment(self):
        return self._compartment

    @compartment.setter
    def compartment(self, value):
        # TODO: Build in logic to set the
        # outer compartment
        # print("Warning: Logical checks are not complete")
        self._compartment = value

    def consolidate_molecule_compartments(self):
        # if the molecule compartment matches overall pattern
        # compartment, don't print the molecule compartments
        overall_comp = self.compartment
        if overall_comp is not None:
            for molec in self.molecules:
                if molec.compartment == overall_comp:
                    molec.compartment = None

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
        # need to make sure we don't print useless compartments
        self.consolidate_molecule_compartments()
        sstr = ""
        # we first deal with the pattern compartment
        if self.compartment is not None:
            sstr += "@{}".format(self.compartment)
        if self.label is not None:
            sstr += "%{}".format(self.label)
        if self.label is not None or self.compartment is not None:
            sstr += ":"
        # now loop over all molecules
        for imol, mol in enumerate(self.molecules):
            if imol == 0:
                if self.fixed:
                    sstr += "$"
                if self.MatchOnce:
                    sstr += "{MatchOnce}"
            if imol > 0:
                sstr += "."
            sstr += str(mol)
        if self.relation is not None:
            sstr += f"{self.relation}{self.quantity}"
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
        self.canonical_order = None
        self.canonical_label = None
        self.parent_pattern = None

    def __contains__(self, val):
        return val in self.components

    def __eq__(self, other):
        loc = f"{__file__} : Molecule.__eq__()"
        # check object type
        if isinstance(other, Molecule):
            logger.debug(f"Comparison class matches: {other.__class__}", loc=loc)
            # check attributes
            if (
                (other.name == self.name)
                and (other.compartment == self.compartment)
                and (other.label == self.label)
            ):
                logger.debug(
                    f"name, compartment and labels match: {other.name}, {other.compartment}, {other.label}",
                    loc=loc,
                )
                if (self.canonical_label is not None) and (
                    other.canonical_label is not None
                ):
                    # we can check canonical labels
                    if self.canonical_label != other.canonical_label:
                        return False
                # check components now
                for component in self:
                    if component not in other.components:
                        logger.debug(f"component doesn't match: {component}", loc=loc)
                        return False
                # everything matches
                logger.debug("molecules match", loc=loc)
                return True
        return False

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.components[key]

    def __iter__(self):
        return self.components.__iter__()

    # TODO: implement __setitem__,  __contains__

    def __str__(self):
        mol_str = self.name
        # we have a null species
        if not self.name == "0":
            mol_str += "("
        # we _could_ just not do () if components
        # don't exist but that has other issues,
        # especially for extension highlighting
        if len(self.components) > 0:
            for icomp, comp in enumerate(self.components):
                if icomp > 0:
                    mol_str += ","
                mol_str += str(comp)
        # we have a null species
        if not self.name == "0":
            mol_str += ")"
        if self.compartment is not None:
            mol_str += "@{}".format(self.compartment)
        if self.label is not None:
            mol_str += "%{}".format(self.label)
        return mol_str

    def print_canonical(self):
        # print in canonical order
        canon_label = self.name
        # we have a null species
        if not self.name == "0":
            canon_label += "("
        # we _could_ just not do () if components
        # don't exist but that has other issues,
        # especially for extension highlighting
        if len(self.components) > 0:
            canon_ords = [c.canonical_order for c in self.components]
            canon_ord_pairs = zip(range(len(self.components)), canon_ords)
            sorted_canon_ord_pairs = sorted(canon_ord_pairs, key=lambda x: x[1])
            for icomp, comp in enumerate(sorted_canon_ord_pairs):
                comp_id = comp[0]
                if icomp > 0:
                    canon_label += ","
                canon_label += self.components[comp_id].print_canonical()
        # we have a null species
        if not self.name == "0":
            canon_label += ")"
        if self.compartment is not None:
            canon_label += "@{}".format(self.compartment)
        if self.label is not None:
            canon_label += "%{}".format(self.label)
        return canon_label

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
        self.canonical_label = None
        self.canonical_order = None
        self.canonical_bonds = None
        self.parent_molecule = None

    def __eq__(self, other):
        loc = f"{__file__} : Component.__eq__()"
        # check type
        # import ipdb;ipdb.set_trace()
        if isinstance(other, Component):
            logger.debug(f"Comparison class matches: {other.__class__}", loc=loc)
            # check attributes
            if (other.name == self.name) and (other.label == self.label):
                logger.debug(
                    f"name and labels match: {other.name}, {other.label}", loc=loc
                )
                # check states
                if len(other.states) == len(self.states):
                    logger.debug(f"state lists match: {other.states}", loc=loc)
                    # check current state
                    if other.state == self.state:
                        logger.debug(f"states match: {other.state}", loc=loc)
                        if (self.canonical_label is not None) and (
                            other.canonical_label is not None
                        ):
                            # we can check canonical labels
                            if self.canonical_label != other.canonical_label:
                                return False
                        # check bonds
                        # TODO: try to decide if A(b!1).B(a!1) is the same
                        # as A(b!2).B(a!2), if so, the bond check is much harder
                        # for bond in self.bonds:
                        #     if bond not in other.bonds:
                        #         logger.debug(
                        #             f"bonds don't match!: {other.bonds}", loc=loc
                        #         )
                        #         return False
                        if len(self.bonds) == len(other.bonds):
                            logger.debug("components match", loc=loc)
                            return True
        return False

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

    def print_canonical(self):
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
        if self.canonical_bonds is not None:
            for bond in self.canonical_bonds:
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
