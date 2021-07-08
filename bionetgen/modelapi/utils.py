import os, subprocess
import bionetgen as bng
from distutils import spawn


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
    # rc = subprocess.run(["perl", bngexec], stdout=bng.defaults.stdout)
    # rc = subprocess.run(["perl", bngexec], capture_output=True, bufsize=1)
    command = ["perl", bngexec]
    rc = run_command(command, suppress=True)
    if rc == 0:
        return True
    else:
        return False


def run_command(command, suppress=False):
    if suppress:
        rc = subprocess.run(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return rc.returncode
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, encoding="utf8")
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                print(output.strip())
        rc = process.poll()
        return rc
