import os, subprocess
import bionetgen as bng
from distutils import spawn

def find_BNG_path(BNGPATH=None):
    '''
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
    '''
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
            print("BNG2.pl seems to be working")
            # get the source of BNG2.pl
            BNGPATH = spawn.find_executable("BNG2.pl")
            BNGPATH, _ = os.path.split(BNGPATH)
    else:
        bngexec = os.path.join(BNGPATH, "BNG2.pl")
        if test_bngexec(bngexec):
            print("BNG2.pl seems to be working")
        else:
            print("BNG2.pl not working, simulator won't run")
    return BNGPATH, bngexec

def test_bngexec(bngexec):
    '''
    A simple function that test if BNG2.pl given runs

    Usage: test_bngexec(path)

    Arguments
    ---------
    bngexec : str
        path to BNG2.pl to test
    '''
    rc = subprocess.run(["perl", bngexec], stdout=bng.defaults.stdout)
    if rc.returncode == 0:
        return True
    else:
        return False

