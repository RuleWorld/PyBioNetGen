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
        raise NotImplementedError
