import bionetgen as bng

from bionetgen.main import BioNetGen
from tempfile import TemporaryFile
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
    recompile : bool
        a tag to keep track if any changes have been made to the model
        via the XML API by the user
    changes : dict
        a list of changes the user have made to the model

    Methods
    -------
    reset_compilation_tags()
        resets compilation tags of each block to keep track of any changes the user
        makes to the model via the API
    add_action(action_type, action_args)
        adds the action of action_type with arguments given by the optional keyword
        argument action_args which is a list of lists where each element
        is of the form [ArgumentName, ArgumentValue]
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
            "compartments",
            "molecule_types",
            "species",
            "observables",
            "functions",
            "rules",
            "actions",
        ]
        self.model_name = ""
        self.bngparser = BNGParser(bngl_model)
        self.bngparser.parse_model(self)
        for block in self.block_order:
            if block not in self.active_blocks:
                self.add_empty_block(block)

    @property
    def recompile(self):
        recompile = False
        for block in self.active_blocks:
            recompile = recompile or getattr(self, block)._recompile
        return recompile

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
        model_str = "begin model\n"
        for block in self.block_order:
            # ensure we didn't get new items into a
            # previously inactive block, if we did
            # add them to the active blocks
            if len(getattr(self, block)) > 0:
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
            getattr(self, i) for i in self.block_order if i in self.active_blocks
        ]
        return active_ordered_blocks.__iter__()

    def add_block(self, block):
        bname = block.name.replace(" ", "_")
        # TODO: fix this exception
        if bname == "reaction_rules":
            bname = "rules"
        block_adder = getattr(self, "add_{}_block".format(bname))
        block_adder(block)

    def add_empty_block(self, block_name):
        bname = block_name.replace(" ", "_")
        # TODO: fix this exception
        if bname == "reaction_rules":
            bname = "rules"
        block_adder = getattr(self, "add_{}_block".format(bname))
        block_adder()

    def add_parameters_block(self, block=None):
        if block is not None:
            assert isinstance(block, ParameterBlock)
            self.parameters = block
            self.active_blocks.append("parameters")
        else:
            self.parameters = ParameterBlock()

    def add_compartments_block(self, block=None):
        if block is not None:
            assert isinstance(block, CompartmentBlock)
            self.compartments = block
            self.active_blocks.append("compartments")
        else:
            self.compartments = CompartmentBlock()

    def add_molecule_types_block(self, block=None):
        if block is not None:
            assert isinstance(block, MoleculeTypeBlock)
            self.molecule_types = block
            self.active_blocks.append("molecule_types")
        else:
            self.molecule_types = MoleculeTypeBlock()

    def add_species_block(self, block=None):
        if block is not None:
            assert isinstance(block, SpeciesBlock)
            self.species = block
            self.active_blocks.append("species")
        else:
            self.species = SpeciesBlock()

    def add_observables_block(self, block=None):
        if block is not None:
            assert isinstance(block, ObservableBlock)
            self.observables = block
            self.active_blocks.append("observables")
        else:
            self.observables = ObservableBlock()

    def add_functions_block(self, block=None):
        if block is not None:
            assert isinstance(block, FunctionBlock)
            self.functions = block
            self.active_blocks.append("functions")
        else:
            self.functions = FunctionBlock()

    def add_rules_block(self, block=None):
        if block is not None:
            assert isinstance(block, RuleBlock)
            self.rules = block
            self.active_blocks.append("rules")
        else:
            self.rules = RuleBlock()

    def add_actions_block(self, block=None):
        if block is not None:
            assert isinstance(block, ActionBlock)
            self.actions = block
            self.active_blocks.append("actions")
        else:
            self.actions = ActionBlock()

    def reset_compilation_tags(self):
        for block in self.active_blocks:
            getattr(self, block).reset_compilation_tags()

    def add_action(self, action_type, action_args=[]):
        # add actions block and to active list
        if not hasattr(self, "actions"):
            self.actions = ActionBlock()
            self.active_blocks.append("actions")
        self.actions.add_action(action_type, action_args)

    def write_model(self, file_name):
        """
        write the model to file
        """
        model_str = ""
        for block in self.active_blocks:
            model_str += str(getattr(self, block))
        with open(file_name, "w") as f:
            f.write(model_str)

    def setup_simulator(self, sim_type="libRR"):
        """
        Sets up a simulator attribute that is a generic front-end
        to all other simulators. At the moment only libroadrunner
        is supported
        """
        if sim_type == "libRR":
            # we need to add writeSBML action for now
            self.add_action("generate_network", [("overwrite", 1)])
            self.add_action("writeSBML", [])
            # temporary file
            with TemporaryFile(mode="w+") as tpath:
                # write the sbml
                self.bngparser.bngfile.write_xml(
                    tpath, xml_type="sbml", bngl_str=str(self)
                )
                # TODO: Only clear the writeSBML action
                # by adding a mechanism to do so
                self.actions.clear_actions()
                # get the simulator
                self.simulator = bng.sim_getter(
                    model_str=tpath.read(), sim_type=sim_type
                )
        else:
            print(
                'Sim type {} is not recognized, only libroadrunner \
                   is supported currently by passing "libRR" to \
                   sim_type keyword argument'.format(
                    sim_type
                )
            )
            return None
        return self.simulator


###### CORE OBJECT AND PARSING FRONT-END ######
