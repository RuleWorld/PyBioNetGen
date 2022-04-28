from .bngsimulator import BNGSimulator

# TODO: Unified API for all simulator objects here
class libRRSimulator(BNGSimulator):
    """
    libRoadRunner simulator wrapper


    Attributes
    ----------
    sbml: str
        the SBML used by the underlying libRoadRunner simulator

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
