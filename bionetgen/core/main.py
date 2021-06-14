from bionetgen.modelapi.utils import run_command
import os, subprocess, shutil
from tempfile import TemporaryDirectory
from sys import stdout
from re import sub
import bionetgen as bng
from bionetgen.core import BNGResult
from bionetgen.core import BNGPlotter

# TODO Consolidate how config is being accessed. It's
# almost like each function accesses the configs from
# a different path 

def runCLI(config, args):
    '''
    Convenience function to run BNG2.pl from the CLI app

    Usage: runCLI(config, args)

    Arguments
    ---------
    config : dict
        configuration dictionary from BioNetGen cement app
    args :  argparse.Namespace
        arguments parsed from the command line with argparser.
    '''
    # this pulls out the arguments
    inp_file = args.input
    output = args.output
    # if you set args.bngpath it should take precedence
    config_bngpath = config.get('bionetgen', 'bngpath')
    # and instantiates the CLI object
    cli = BNGCLI(inp_file, output, config_bngpath)
    cli.stdout = config.get("bionetgen", "stdout")
    cli.stderr = config.get("bionetgen", "stderr")
    cli.run()

def plotDAT(inp, out=".", kw=dict()):
    '''
    Convenience function to plot dat/scan files from the CLI

    Usage: plotDAT(inp, out, kw)

    Arguments
    ---------
    inp : str
        input gdat/cdat/scan file to plot
    out : str 
        (optional) output file path, can be used to define the
        output format as well. Default is the current folder, 
        filename is the same as the input file and default format
        is PNG.
    kw : dict
        (optional) this is a set of keyword arguments you want to 
        pass for certain matplotlib options. Check -h for details
    '''
    # if we want to plot directly into the folder
    # we are in we need to get the path correctly
    if out == ".":
        path, fname = os.path.split(inp)
        fnoext, ext = os.path.splitext(fname)
        out = os.path.join(path, "{}.png".format(fnoext))
    # use the plotter object to get the plot
    plotter = BNGPlotter(inp, out, **kw)
    plotter.plot()

class BNGCLI:
    '''
    Command Line Interface class to run BNG2.pl on a given
    model. 

    Usage: BNGCLI(inp_file, output, bngpath)

    Arguments
    ---------
    inp_file : str
        path to the the BNGL file to run
    output : str 
        path to the output folder to run the model in
    bngpath : str
        path to BioNetGen folder where BNG2.pl lives
    
    Methods
    -------
    run()
        runs the model in the given output folder
    '''
    def __init__(self, inp_file, output, bngpath):
        self.inp_file = inp_file
        # ensure correct path to the input file
        self.inp_path = os.path.abspath(self.inp_file)
        # pull other arugments out
        self._set_output(output)
        # sedml_file = sedml
        self.bngpath = bngpath
        # setting up bng2.pl
        self.bng_exec = os.path.join(self.bngpath, "BNG2.pl")
        assert os.path.exists(self.bng_exec), "BNG2.pl is not found!"
        if "BNGPATH" in os.environ:
            self.old_bngpath = os.environ["BNGPATH"]
        else:
            self.old_bngpath = None
        os.environ["BNGPATH"] = self.bngpath
        self.result = None
        self.stdout = "PIPE"
        self.stderr = "STDOUT"

    def _set_output(self, output):
        # setting up output area
        self.output = output
        if os.path.isdir(output):
            # path exists, let's go there
            os.chdir(output)
        else:
            os.mkdir(output)
            os.chdir(output)

    def run(self):
        try: 
            stdout_loc = getattr(subprocess, self.stdout)
        except:
            stdout_loc = subprocess.PIPE
        try: 
            stderr_loc = getattr(subprocess, self.stderr)
        except:
            stderr_loc = subprocess.STDOUT
        # run BNG2.pl
        # rc = subprocess.run(["perl", self.bng_exec, self.inp_path], stdout=stdout_loc, stderr=stderr_loc)
        # rc = subprocess.run(["perl", self.bng_exec, self.inp_path], capture_output=True, bufsize=1)
        command = ["perl", self.bng_exec, self.inp_path]
        rc = run_command(command)
        # write out stdout/err if they exist
        # TODO Maybe indicate that we are printing out stdout/stderr before printing
        # if rc.stdout is not None:
        #     print(rc.stdout.decode('utf-8'))
        # if rc.stderr is not None:
        #     print(rc.stderr.decode('utf-8'))
        if rc == 0:
            # load in the result 
            self.result = BNGResult(os.getcwd())
            BNGResult.process_return = rc
        else:
            self.result = None
        # set BNGPATH back
        if self.old_bngpath is not None:
            os.environ["BNGPATH"] = self.old_bngpath

