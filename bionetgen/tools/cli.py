import os, subprocess


class BNGCLI:
    """
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
    """

    def __init__(self, inp_file, output, bngpath, suppress=False, log_file=None):
        self.inp_file = inp_file
        import bionetgen.modelapi.model as mdl

        if isinstance(inp_file, mdl.bngmodel):
            self.is_bngmodel = True
        else:
            self.is_bngmodel = False
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
        self.suppress = suppress
        self.log_file = log_file

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
        from bionetgen.modelapi.utils import run_command

        try:
            stdout_loc = getattr(subprocess, self.stdout)
        except:
            stdout_loc = subprocess.PIPE
        try:
            stderr_loc = getattr(subprocess, self.stderr)
        except:
            stderr_loc = subprocess.STDOUT
        # run BNG2.pl
        if self.is_bngmodel:
            write_to = self.inp_file.model_name + ".bngl"
            write_to = os.path.abspath(write_to)
            if os.path.isfile(write_to):
                print(f"WARNIING: Overwriting file {write_to}")
            with open(write_to, "w") as tfile:
                tfile.write(str(self.inp_file))
            command = ["perl", self.bng_exec, write_to]
        else:
            fname = os.path.basename(self.inp_path)
            fname = fname.replace(".bngl", "")
            command = ["perl", self.bng_exec, self.inp_path]
        rc, out = run_command(command, suppress=self.suppress)
        if self.log_file is not None:
            # test if we were given a path
            # TODO: This is a simple hack, might need to adjust it
            # trying to check if given file is an absolute/relative
            # path and if so, use that one. Otherwise, divine the
            # current path.
            if os.path.exists(self.log_file):
                # file or folder exists, check if folder
                if os.path.isdir(self.log_file):
                    fname = os.path.basename(self.inp_path)
                    fname = fname.replace(".bngl", "")
                    full_log_path = os.path.join(self.log_file, fname + ".log")
                else:
                    # it's intended to be file, so we keep it as is
                    full_log_path = self.log_file
            else:
                # doesn't exist, so we assume it's a file
                # and we keep it as is
                full_log_path = self.log_file

            with open(full_log_path, "w") as f:
                f.write("\n".join(out))

        # if self.is_bngmodel:
        #     os.remove(tfile.name)
        # write out stdout/err if they exist
        # TODO Maybe indicate that we are printing out stdout/stderr before printing
        # if rc.stdout is not None:
        #     print(rc.stdout.decode('utf-8'))
        # if rc.stderr is not None:
        #     print(rc.stderr.decode('utf-8'))
        if rc == 0:
            from bionetgen.tools import BNGResult

            # load in the result
            self.result = BNGResult(os.getcwd())
            BNGResult.process_return = rc
            # set BNGPATH back
            if self.old_bngpath is not None:
                os.environ["BNGPATH"] = self.old_bngpath
        else:
            self.result = None
            # set BNGPATH back
            if self.old_bngpath is not None:
                os.environ["BNGPATH"] = self.old_bngpath
            raise ValueError(
                "Failed to run your BNGL file, there might be an issue with your model!"
            )
