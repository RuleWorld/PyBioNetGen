import os
from tempfile import TemporaryDirectory
from bionetgen.main import BioNetGen
from bionetgen.tools import BNGCLI

# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config["bionetgen"]


def run(inp, out=None, suppress=False):
    """
    Convenience function to run BNG2.pl as a library

    Usage: run(path_to_input_file, output_folder)

    Arguments
    ---------
    path_to_input_file : str
        this has to point to a BNGL file
    output_folder : str
        (optional) this points to a folder to put the results
        into. If it doesn't exist, it will be created.
    """
    # if out is None we make a temp directory
    cur_dir = os.getcwd()
    if out is None:
        with TemporaryDirectory() as out:
            # instantiate a CLI object with the info
            cli = BNGCLI(inp, out, conf["bngpath"], suppress=suppress)
            try:
                cli.run()
                os.chdir(cur_dir)
            except Exception as e:
                os.chdir(cur_dir)
                # TODO: Better error reporting
                print("Couldn't run the simulation")
                print(e)
                raise
    else:
        # instantiate a CLI object with the info
        cli = BNGCLI(inp, out, conf["bngpath"], suppress=suppress)
        try:
            cli.run()
            os.chdir(cur_dir)
        except Exception as e:
            os.chdir(cur_dir)
            # TODO: Better error reporting
            print("Couldn't run the simulation")
            print(e)
            raise
    return cli.result
