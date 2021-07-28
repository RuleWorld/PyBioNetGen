import os
import subprocess
import bionetgen as bng
from distutils import spawn


class ActionList:
    def __init__(self):
        self.normal_types = [
            "generate_network",
            "generate_hybrid_model",
            "simulate",
            "simulate_ode",
            "simulate_ssa",
            "simulate_pla",
            "simulate_nf",
            "parameter_scan",
            "bifurcate",
            "readFile",
            "writeFile",
            "writeModel",
            "writeNetwork",
            "writeXML",
            "writeSBML",
            "writeMfile",
            "writeMexfile",
            "writeMDL",
            "visualize",
        ]
        self.no_setter_syntax = [
            "setConcentration",
            "addConcentration",
            "setParameter",
            "saveParameters",
            "quit",
            "setModelName",
            "substanceUnits",
            "version",
            "setOption",
        ]
        self.square_braces = [
            "saveConcentrations",
            "resetConcentrations",
            "resetParameters",
        ]
        self.possible_types = (
            self.normal_types + self.no_setter_syntax + self.square_braces
        )


def find_BNG_path(BNGPATH=None):
    """
    A simple function finds the path to BNG2.pl from
    * Environment variable
    * Assuming it's under PATH
    * Given optional path as argument

    Usage: test_bngexec(path)
           test_bngexec()

    Arguments
    ---------
    BNGPATH : str
        (optional) path to the folder that contains BNG2.pl
    """
    # TODO: Figure out how to use the BNG2.pl if it's set
    # in the PATH variable. Solution: set os.environ BNGPATH
    # and make everything use that route

    # Let's keep up the idea we pull this path from the environment
    if BNGPATH is None:
        try:
            BNGPATH = os.environ["BNGPATH"]
        except:
            pass
    # if still none, try pulling it from cmd line
    if BNGPATH is None:
        bngexec = "BNG2.pl"
        if test_bngexec(bngexec):
            # print("BNG2.pl seems to be working")
            # get the source of BNG2.pl
            BNGPATH = spawn.find_executable("BNG2.pl")
            BNGPATH, _ = os.path.split(BNGPATH)
    else:
        bngexec = os.path.join(BNGPATH, "BNG2.pl")
        if not test_bngexec(bngexec):
            RuntimeError("BNG2.pl is not working")
    return BNGPATH, bngexec


def test_bngexec(bngexec):
    """
    A simple function that test if BNG2.pl given runs

    Usage: test_bngexec(path)

    Arguments
    ---------
    bngexec : str
        path to BNG2.pl to test
    """
    command = ["perl", bngexec]
    rc, _ = run_command(command, suppress=True)
    if rc == 0:
        return True
    else:
        return False


def run_command(command, suppress=False):
    if suppress:
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1
        )
        return process.poll(), None
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, encoding="utf8")
        out = []
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                o = output.strip()
                out.append(o)
                print(o)
        rc = process.poll()
        return rc, out
