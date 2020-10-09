import os, subprocess

def runCLI(args):
    cli = BNGCLI(args)
    cli.run()

class BNGCLI:
    def __init__(self, args):
        self.inp_file = args.input
        # ensure correct path to the input file
        self.inp_path = os.path.abspath(self.inp_file)
        # pull other arugments out
        self.set_output(args.output)
        # sedml_file = args.sedml
        self.bngpath = args.bngpath
        # setting up bng2.pl
        self.bng_exec = os.path.join(self.bngpath, "BNG2.pl")
        assert os.path.exists(self.bng_exec), "BNG2.pl is not found!"
        if "BNGPATH" in os.environ:
            self.old_bngpath = os.environ["BNGPATH"]
        else:
            self.old_bngpath = None
        os.environ["BNGPATH"] = self.bngpath

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
        # set BNGPATH back
        if self.old_bngpath is not None:
            os.environ["BNGPATH"] = self.old_bngpath
