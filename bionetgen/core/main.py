import os, subprocess, shutil, tempfile
from sys import stdout
from re import sub
import bionetgen as bng
from bionetgen.core import BNGResult
from bionetgen.core import BNGPlotter

def run(inp, out=None):
    '''
    Convenience function to run BNG2.pl from python

    Usage: run(path_to_input_file, output_folder)

    path_to_input_file: this has to point to a BNGL file

    output_folder: this points to a folder to put 
    the results into. If it doesn't exist, it will be 
    created.
    '''
    # if out is None we make a temp directory
    if out is None:
        temp = True
        out = tempfile.mkdtemp()
        cur_dir = os.getcwd()
    else:
        temp = False
    # instantiate a CLI object with the info
    cli = BNGCLI(inp, out, bng.defaults.config.get("bionetgen", "bngpath"))
    cli.run()
    # if we used a temporary directory, clean up
    if temp: 
        shutil.rmtree(out)
        os.chdir(cur_dir)
    print(cli.result.process_return.stdout)
    return cli.result

def runCLI(config, args):
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
    def __init__(self, inp_file, output, bngpath):
        self.inp_file = inp_file
        # ensure correct path to the input file
        self.inp_path = os.path.abspath(self.inp_file)
        # pull other arugments out
        self.set_output(output)
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

    def set_output(self, output):
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
        rc = subprocess.run(["perl", self.bng_exec, self.inp_path], stdout=stdout_loc, stderr=stderr_loc)
        # write out stdout/err if they exist
        # TODO Maybe indicate that we are printing out stdout/stderr before printing
        if rc.stdout is not None:
            print(rc.stdout.decode('utf-8'))
        if rc.stderr is not None:
            print(rc.stderr.decode('utf-8'))
        # load in the result 
        self.result = BNGResult(os.getcwd())
        BNGResult.process_return = rc
        # set BNGPATH back
        if self.old_bngpath is not None:
            os.environ["BNGPATH"] = self.old_bngpath

