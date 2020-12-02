def sim_getter(model_file, sim_type="libRR"):
    if sim_type == "libRR":
        return libRRSimulator(model_file)
    else:
        print("simulator type {} not supported".format(sim_type))

# TODO: Unified API for all simulator objects here
class libRRSimulator:
    def __init__(self, model_file):
        # this also sets up simulator attribute
        self.model_file = model_file
    
    @property
    def model_file(self):
        return self._model_file
    
    @model_file.setter
    def model_file(self, mfile):
        self._model_file = mfile
        self.simulator = mfile

    @property
    def simulator(self):
        return self._simulator

    @simulator.setter
    def simulator(self, mfile):
        try: 
            import roadrunner as rr
            self._simulator = rr.RoadRunner(mfile)
            self.sbml = self._simulator
        except ImportError:
            print("libroadrunner is not installed!")

    @property
    def sbml(self):
        return self._sbml
    
    @sbml.setter
    def sbml(self, librr):
        self._sbml = librr.getCurrentSBML()

    def simulate(self, *args, **kwargs):
        return self.simulator.simulate(*args, **kwargs)

