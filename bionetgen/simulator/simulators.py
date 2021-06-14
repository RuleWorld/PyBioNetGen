def sim_getter(model_file=None, model_str=None, sim_type="libRR"):
    """
    Convenience function to get a simulator object of a specific type.
    Allows you to pull a simulator object given a model file path.

    Note: This likely needs to be refactored but for now it works.

    Parameters
    ----------
    model_file : str, optional
        The path to the model file, at the moment only BNGL is expected
        but this can change in the future.
    model_str : str, optional
        Instead of the path to the model you can also supply the model
        string instead.
    sim_type : str, optional
        The name of the type of simulator object to get. At the moment only
        libRoadRunner type simulators are allowed. This will get updated
        as differenty types of simulators are added.

    Returns
    -------
    BNGSimulator
        A simulator object with an API that's supposed to be agnostic to the
        underlying simulator it's running.
    """
    if model_file is not None:
        if sim_type == "libRR":
            return libRRSimulator(model_file=model_file)
        else:
            print("simulator type {} not supported".format(sim_type))
    elif model_str is not None:
        if sim_type == "libRR":
            return libRRSimulator(model_str=model_str)
        else:
            print("simulator type {} not supported".format(sim_type))


class BNGSimulator:
    """
    The generic simulator interface to all BNG simulators.

    This is (going to be) designed to allow for a generic API to all
    other types of simulators so that this API can be used in the rest
    of the library without specifically writing code for each simulator
    type.


    Attributes
    ----------
    model_file : str
        path to the model file this simulator is using

    Properties
    ----------
    simulator: obj
        the python object that runs the actual simulation.
        Any subclass implementing a BNGSimulator should set
        this property and make it so that setting the simulator
        object to the file path given to initialize the
        BNGSimulator class initializes the simulator object in turn.

    Methods
    -------
    simulate(args)
        Uses the arguments provided to call the underlying simulator
    """

    def __init__(self, model_file=None, model_str=None):
        """
        This class is inialized by giving it the path to the model file
        you want it to open and run.
        """
        # this also sets up simulator attribute
        if model_file is not None:
            self.model_file = model_file
        if model_str is not None:
            self.model_str = model_str

    @property
    def model_file(self):
        """
        model file attribute that stores the path to the original
        model file and also sets up the simulator
        """
        return self._model_file

    @model_file.setter
    def model_file(self, mfile):
        self._model_file = mfile
        self.simulator = mfile

    @property
    def model_str(self):
        """
        model file attribute that stores the path to the original
        model file and also sets up the simulator
        """
        return self._model_str

    @model_str.setter
    def model_str(self, mstr):
        self._model_str = mstr
        self.simulator = mstr

    def simulate(self):
        return


# TODO: Unified API for all simulator objects here
class libRRSimulator(BNGSimulator):
    """
    libRoadRunner simulator wrapper


    Attributes
    ----------
    sbml: str
        the SBML used by the underlying libRoarRunner simulator

    Properties
    ----------
    simulator: obj
        the python object that runs the actual simulation.
        Any subclass implementing a BNGSimulator should set
        this property and make it so that setting the simulator
        object to the file path given to initialize the
        BNGSimulator class initializes the simulator object in turn.

    Methods
    -------
    simulate(args)
        Uses the arguments provided to call the underlying simulator
    """

    @property
    def simulator(self):
        """
        simulator attribute that stores
        the instantiated simulator object
        and also saves the SBML text in the
        sbml attribute
        """
        return self._simulator

    @simulator.setter
    def simulator(self, model):
        try:
            import roadrunner as rr

            self._simulator = rr.RoadRunner(model)
        except ImportError:
            print("libroadrunner is not installed!")

    @property
    def sbml(self):
        """
        sbml attribute which is just the SBML
        string with which the libRR instance
        is instantiated with
        """
        if not hasattr(self, "_sbml"):
            self._sbml = self.simulator.getCurrentSBML()
        return self._sbml

    @sbml.setter
    def sbml(self, model_str):
        self._sbml = model_str

    def simulate(self, *args, **kwargs):
        """
        generic simulate front-end that passes the
        args and kwargs to the underlying simulator object
        """
        return self.simulator.simulate(*args, **kwargs)
