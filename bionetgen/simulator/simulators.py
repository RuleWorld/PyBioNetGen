from .librrsimulator import libRRSimulator
from .csimulator import CSimulator


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
    if model_str is not None and model_file is None:
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile("w+") as model_file_obj:
            model_file_obj.write(model_str)
            model_file = model_file_obj.name
            if sim_type == "libRR":
                # need to go back to beginning of the file for this to work
                model_file_obj.seek(0)
                return libRRSimulator(model_file=model_file)
            elif sim_type == "cpy":
                return CSimulator(model_file=model_file, generate_network=True)
            else:
                print("simulator type {} not supported".format(sim_type))
    if model_file is not None:
        if sim_type == "libRR":
            return libRRSimulator(model_file=model_file)
        elif sim_type == "cpy":
            return CSimulator(model_file=model_file, generate_network=True)
        else:
            print("simulator type {} not supported".format(sim_type))
