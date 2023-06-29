import copy, tempfile, shutil

from bionetgen.main import BioNetGen
from bionetgen.core.exc import BNGModelError

from .bngparser import BNGParser
from .blocks import (
    ActionBlock,
    CompartmentBlock,
    FunctionBlock,
    MoleculeTypeBlock,
    ObservableBlock,
    ParameterBlock,
    RuleBlock,
    SpeciesBlock,
    EnergyPatternBlock,
    PopulationMapBlock,
)


# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config["bionetgen"]
def_bng_path = conf["bngpath"]


###### CORE OBJECT AND PARSING FRONT-END ######
class bngmodel:
    """
    Main model object and entry point for model API. The goal of this
    object is to generate and read the BNGXML of a given BNGL model
    and give the user a pythonic interface to the resulting model object.

    Usage: bngmodel(bng_model)
           bngmodel(bng_model, BNGPATH)

    Attributes
    ----------
    active_blocks : list[str]
        a list of the blocks that have been parsed in the model
    bngparser : BNGParser
        BNGParser object that's responsible for .bngl file reading and model setup
    model_name : str
        name of the model, generally set from the given BNGL file
    model_path : str
        path to the model file initially given
    recompile : bool
        a tag to keep track if any changes have been made to the model
        via the XML API by the user that requires model recompilation
    changes : dict
        a list of changes the user have made to the model

    Methods
    -------
    reset_compilation_tags()
        resets compilation tags of each block to keep track of any changes the user
        makes to the model via the API
    add_action(action_type, action_args)
        adds the action of action_type with arguments given by the optional keyword
        argument action_args, which is a dictionary where each element
        is of the form "ArgumentName":ArgumentValue
    write_model(model_name)
        write the model in BNGL format to the path given
    setup_simulator(sim_type)
        sets up a simulator in bngmodel.simulator where the only current supported
        type of simulator is libRR for libRoadRunner simulator.
    add_block(BlockObject)
        adds a given block object (e.g. ParametersBlock) to the model
    add_empty_block(block_type)
        adds an empty block of type block_type to the model where block_type can be one of: "parameters",
        "compartments", "molecule_types", "species", "observables", "functions", "energy_patterns",
        "population_maps", "rules", "reaction_rules", "actions".
    """

    def __init__(
        self, bngl_model, BNGPATH=def_bng_path, generate_network=False, suppress=True
    ):
        self.active_blocks = []
        # We want blocks to be printed in the same order every time
        self._block_order = [
            "parameters",
            "compartments",
            "molecule_types",
            "species",
            "observables",
            "functions",
            "energy_patterns",
            "population_maps",
            "rules",
            "actions",
        ]
        self.model_name = ""
        self.model_path = bngl_model
        self.bngparser = BNGParser(
            bngl_model, generate_network=generate_network, suppress=True
        )
        self.bngparser.parse_model(self)
        for block in self._block_order:
            if block not in self.active_blocks:
                self.add_empty_block(block)
        # Check to see if there are no active blocks
        # If not, model is most likely not in BNGL format
        if not self.active_blocks:
            # TODO: consider raising a BNGModelError() here
            # raise BNGModelError(
            #                 self.model_path,
            #                 message="WARNING: No active blocks. Please ensure model is in proper BNGL or BNG-XML format",
            #             )
            print(
                "WARNING: No active blocks. Please ensure model is in proper BNGL or BNG-XML format"
            )

    @property
    def recompile(self):
        recompile = False
        for block in self.active_blocks:
            recompile = recompile or getattr(self, block)._recompile
        return recompile

    # TODO: Ensure this works when you edit attributes
    @property
    def changes(self):
        changes = {}
        for block in self.active_blocks:
            changes[block] = getattr(self, block)._changes
        return changes

    def __str__(self):
        """
        write the model to str
        """
        model_str = ""
        # gotta check for "before model" type actions
        if hasattr(self, "actions"):
            ablock = getattr(self, "actions")
            if len(ablock.before_model) > 0:
                for baction in ablock.before_model:
                    model_str += str(baction) + "\n"
        model_str += "begin model\n"
        for block in self._block_order:
            # ensure we didn't get new items into a
            # previously inactive block, if we did
            # add them to the active blocks
            if hasattr(self, block):
                if len(getattr(self, block)) > 0:
                    if getattr(self, block).name not in self.active_blocks:
                        self.active_blocks.append(block)
                # if we removed items from a block and
                # it's now empty, we want to remove it
                # from the active blocks
                elif len(getattr(self, block)) == 0 and block in self.active_blocks:
                    self.active_blocks.remove(block)
            # print only the active blocks
            if block in self.active_blocks:
                if block != "actions" and len(getattr(self, block)) > 0:
                    model_str += str(getattr(self, block))
        model_str += "\nend model\n\n"
        if "actions" in self.active_blocks:
            model_str += str(self.actions)
        return model_str

    def __repr__(self):
        return self.model_name

    def __iter__(self):
        active_ordered_blocks = [
            getattr(self, i) for i in self._block_order if i in self.active_blocks
        ]
        return active_ordered_blocks.__iter__()

    def add_block(self, block):
        """
        Adds the given block object to the model, uses the
        name of the block object to determine what block it is
        """
        bname = block.name.replace(" ", "_")
        # TODO: fix this exception
        if bname == "reaction_rules":
            bname = "rules"
        block_adder = getattr(self, "add_{}_block".format(bname))
        block_adder(block)

    def add_empty_block(self, block_name):
        """
        Makes an empty block object from a given block name and
        adds it to the model object.
        """
        bname = block_name.replace(" ", "_")
        # TODO: fix this exception
        if bname == "reaction_rules":
            bname = "rules"
        block_adder = getattr(self, "add_{}_block".format(bname))
        block_adder()

    def add_parameters_block(self, block=None):
        """
        Adds a parameters block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, ParameterBlock)
            self.parameters = block
            if "parameters" not in self.active_blocks:
                self.active_blocks.append("parameters")
        else:
            self.parameters = ParameterBlock()

    def add_compartments_block(self, block=None):
        """
        Adds a compartments block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, CompartmentBlock)
            self.compartments = block
            if "compartments" not in self.active_blocks:
                self.active_blocks.append("compartments")
        else:
            self.compartments = CompartmentBlock()

    def add_molecule_types_block(self, block=None):
        """
        Adds a molecule types block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, MoleculeTypeBlock)
            self.molecule_types = block
            if "molecule_types" not in self.active_blocks:
                self.active_blocks.append("molecule_types")
        else:
            self.molecule_types = MoleculeTypeBlock()

    def add_species_block(self, block=None):
        """
        Adds a species block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, SpeciesBlock)
            self.species = block
            if "species" not in self.active_blocks:
                self.active_blocks.append("species")
        else:
            self.species = SpeciesBlock()

    def add_observables_block(self, block=None):
        """
        Adds an observable block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, ObservableBlock)
            self.observables = block
            if "observables" not in self.active_blocks:
                self.active_blocks.append("observables")
        else:
            self.observables = ObservableBlock()

    def add_functions_block(self, block=None):
        """
        Adds a functions block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, FunctionBlock)
            self.functions = block
            if "functions" not in self.active_blocks:
                self.active_blocks.append("functions")
        else:
            self.functions = FunctionBlock()

    def add_rules_block(self, block=None):
        """
        Adds a rules block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, RuleBlock)
            self.rules = block
            if "rules" not in self.active_blocks:
                self.active_blocks.append("rules")
        else:
            self.rules = RuleBlock()

    def add_energy_patterns_block(self, block=None):
        """
        Adds an energy patterns block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, EnergyPatternBlock)
            self.energy_patterns = block
            if "energy_patterns" not in self.active_blocks:
                self.active_blocks.append("energy_patterns")
        else:
            self.energy_patterns = EnergyPatternBlock()

    def add_population_maps_block(self, block=None):
        """
        Adds a population maps block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, PopulationMapBlock)
            self.population_maps = block
            if "population_maps" not in self.active_blocks:
                self.active_blocks.append("population_maps")
        else:
            self.population_maps = PopulationMapBlock()

    def add_actions_block(self, block=None):
        """
        Adds an actions block to the model object.
        """
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, ActionBlock)
            self.actions = block
            if "actions" not in self.active_blocks:
                self.active_blocks.append("actions")
        else:
            self.actions = ActionBlock()

    def reset_compilation_tags(self):
        """
        This function resets all internal tags used for keeping
        track of changes done to a model after it's loaded. Resetting
        these tags will remove all history of changes.
        """
        for block in self.active_blocks:
            getattr(self, block).reset_compilation_tags()

    def add_action(self, action_type, action_args={}):
        """
        Adds an action to the actions block of the model object.
        If an actions block doesn't exist, this will make an empty
        actions block and append the action to the block.

        Arguments
        ---------
        action_type: str
            the type of action being added
        action_args: dict
            a dictionary where the key is the argument type and the value
            is the value of that argument.
        """
        # add actions block and to active list
        if not hasattr(self, "actions"):
            self.actions = ActionBlock()
            if "actions" not in self.active_blocks:
                self.active_blocks.append("actions")
        self.actions.add_action(action_type, action_args)

    def write_model(self, file_name):
        """
        write the model to file
        """
        with open(file_name, "w") as f:
            f.write(str(self))

    def setup_simulator(self, sim_type="libRR"):
        """
        Sets up a simulator attribute that is a generic front-end
        to all other simulators. At the moment only libroadrunner
        is supported
        """
        if sim_type == "libRR":
            # we need to add writeSBML action for now
            curr_actions = copy.deepcopy(self.actions)
            self.actions.clear_actions()
            self.add_action("generate_network", {"overwrite": 1})
            self.add_action("writeSBML", {})
            # temporary folder instead to make it work
            # with windows
            try:
                tmp_folder = tempfile.mkdtemp()
                sbml_name = f"{self.model_name}_sbml.xml"
                # write the sbml
                with open(sbml_name, "w+") as f:
                    if not (
                        self.bngparser.bngfile.write_xml(
                            f, xml_type="sbml", bngl_str=str(self)
                        )
                    ):
                        raise BNGModelError(
                            self.model_path,
                            message="SBML couldn't be generated for libRR simulator",
                        )
                self.actions.clear_actions()
                # get the simulator
                import bionetgen as bng

                self.simulator = bng.sim_getter(model_file=sbml_name, sim_type=sim_type)
                # let's deal with observables here
                selections = ["time"] + [obs for obs in self.observables]
                self.simulator.simulator.timeCourseSelections = selections
            finally:
                shutil.rmtree(tmp_folder)
            self.actions = curr_actions
        elif sim_type == "cpy":
            # get the simulator
            import bionetgen as bng

            self.simulator = bng.sim_getter(model_file=self, sim_type=sim_type)
            return self.simulator
        else:
            print(
                'Sim type {} is not recognized, only libroadrunner \
                   is supported currently by passing "libRR" to \
                   sim_type keyword argument'.format(
                    sim_type
                )
            )
            return None
        # for now we return the underlying simulator
        return self.simulator.simulator


###### CORE OBJECT AND PARSING FRONT-END ######
