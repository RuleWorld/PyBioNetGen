from bionetgen.main import BioNetGen
from bionetgen.network.networkparser import BNGNetworkParser
from bionetgen.network.blocks import (
    NetworkGroupBlock,
    NetworkParameterBlock,
    NetworkReactionBlock,
    NetworkSpeciesBlock,
    NetworkCompartmentBlock,
    NetworkFunctionBlock,
    NetworkEnergyPatternBlock,
    NetworkPopulationMapBlock,
)


# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config["bionetgen"]
def_bng_path = conf["bngpath"]

###### CORE OBJECT AND PARSING FRONT-END ######
class Network:
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
    bngnetworkparser : BNGNetworkParser
        BNGParser object that's responsible for .bngl file reading and model setup
    network_name : str
        name of the model, generally set from the given BNGL file

    Methods
    -------
    write_model(model_name)
        write the model in BNGL format to the path given
    setup_simulator(sim_type)
        sets up a simulator in bngmodel.simulator where the only current supported
        type of simulator is libRR for libRoadRunner simulator.
    """

    def __init__(self, bngl_model, BNGPATH=def_bng_path):
        self.active_blocks = []
        # We want blocks to be printed in the same order every time
        self.block_order = [
            "parameters",
            "species",
            "reactions",
            "groups"
            # "compartments",
            # "molecule_types",
            # "species",
            # "functions",
            # "energy_patterns",
            # "population_maps",
            # "actions",
        ]
        self.network_name = ""
        self.bngnetworkparser = BNGNetworkParser(bngl_model)
        self.bngnetworkparser.parse_network(self)
        for block in self.block_order:
            if block not in self.active_blocks:
                self.add_empty_block(block)
        # Check to see if there are no active blocks
        # If not, model is most likely not in BNGL format
        if not self.active_blocks:
            print(
                "WARNING: No active blocks. Please ensure model is in proper BNGL or BNG-XML format"
            )

    def __str__(self):
        """
        write the model to str
        """
        model_str = ""
        for block in self.block_order:
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
        return model_str

    def __repr__(self):
        return self.network_name

    def __iter__(self):
        active_ordered_blocks = [
            getattr(self, i) for i in self.block_order if i in self.active_blocks
        ]
        return active_ordered_blocks.__iter__()

    def add_block(self, block):
        bname = block.name.replace(" ", "_")
        # TODO: fix this exception
        block_adder = getattr(self, "add_{}_block".format(bname))
        block_adder(block)

    def add_empty_block(self, block_name):
        bname = block_name.replace(" ", "_")
        # TODO: fix this exception
        block_adder = getattr(self, "add_{}_block".format(bname))
        block_adder()

    def add_parameters_block(self, block=None):
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, NetworkParameterBlock)
            self.parameters = block
            if "parameters" not in self.active_blocks:
                self.active_blocks.append("parameters")
        else:
            self.parameters = NetworkParameterBlock()

    # def add_compartments_block(self, block=None):
    #     if block is not None:
    #         assert isinstance(block, NetworkCompartmentBlock)
    #         self.compartments = block
    #         if "compartments" not in self.active_blocks:
    #             self.active_blocks.append("compartments")
    #     else:
    #         self.compartments = NetworkCompartmentBlock()

    def add_species_block(self, block=None):
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, NetworkSpeciesBlock)
            self.species = block
            if "species" not in self.active_blocks:
                self.active_blocks.append("species")
        else:
            self.species = NetworkSpeciesBlock()

    def add_groups_block(self, block=None):
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, NetworkGroupBlock)
            self.groups = block
            if "groups" not in self.active_blocks:
                self.active_blocks.append("groups")
        else:
            self.groups = NetworkGroupBlock()

    def add_reactions_block(self, block=None):
        if block is not None:
            # TODO: Transition to BNGErrors and logging
            assert isinstance(block, NetworkReactionBlock)
            self.reactions = block
            if "reactions" not in self.active_blocks:
                self.active_blocks.append("reactions")
        else:
            self.reactions = NetworkReactionBlock()

    # def add_functions_block(self, block=None):
    #     if block is not None:
    #         assert isinstance(block, NetworkFunctionBlock)
    #         self.functions = block
    #         if "functions" not in self.active_blocks:
    #             self.active_blocks.append("functions")
    #     else:
    #         self.functions = NetworkFunctionBlock()

    # def add_energy_patterns_block(self, block=None):
    #     if block is not None:
    #         assert isinstance(block, NetworkEnergyPatternBlock)
    #         self.energy_patterns = block
    #         if "energy_patterns" not in self.active_blocks:
    #             self.active_blocks.append("energy_patterns")
    #     else:
    #         self.energy_patterns = NetworkEnergyPatternBlock()

    # def add_population_maps_block(self, block=None):
    #     if block is not None:
    #         assert isinstance(block, NetworkPopulationMapBlock)
    #         self.population_maps = block
    #         if "population_maps" not in self.active_blocks:
    #             self.active_blocks.append("population_maps")
    #     else:
    #         self.population_maps = NetworkPopulationMapBlock()

    def write_model(self, file_name):
        """
        write the model to file
        """
        model_str = ""
        for block in self.active_blocks:
            model_str += str(getattr(self, block))
        with open(file_name, "w") as f:
            f.write(model_str)
