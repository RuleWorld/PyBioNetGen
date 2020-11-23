def sim_getter(model_file, sim_type="libRR"):
    if sim_type == "libRR":
        return libRRSimulator(model_file)
    else:
        print("simulator type {} not supported".format(sim_type))
    
# TODO: Unified API for all simulator objects here
class libRRSimulator:
    def __init__(self, model_file):
        try:
            import roadrunner as rr
            self._simulator = rr.RoadRunner(model_file)
        except ImportError:
            print("libroadrunner is not installed!")
