import os, subprocess, shutil, tempfile, platform
from bionetgen.core import BNGResult

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
    # pull bngpath relative to our file name
    lib_path = os.path.split(os.path.dirname(__file__))[0]
    # determine what bng we are using
    system = platform.system() 
    if system == "Linux":
        bng_name = "bng-linux"
    elif system == "Windows":
        bng_name = "bng-win"
    elif system == "Darwin":
        bng_name = "bng-mac"
    # get bng path
    bngpath = os.path.join(lib_path, bng_name)
    # instantiate a CLI object with the info
    cli = BNGCLI(inp, out, bngpath)
    cli.run()
    # if we used a temporary directory, clean up
    if temp: 
        shutil.rmtree(out)
        os.chdir(cur_dir)
    return cli.result

def runCLI(args):
    # this pulls out the arguments
    inp_file = args.input
    output = args.output
    bngpath = args.bngpath 
    # and instantiates the CLI object
    cli = BNGCLI(inp_file, output, bngpath)
    cli.run()

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
        # run BNG2.pl
        rc = subprocess.run(["perl", self.bng_exec, self.inp_path])
        # load in the result 
        self.result = BNGResult(os.getcwd())
        # set BNGPATH back
        if self.old_bngpath is not None:
            os.environ["BNGPATH"] = self.old_bngpath
