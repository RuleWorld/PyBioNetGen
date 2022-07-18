import os, glob
from pytest import raises
import bionetgen as bng
from bionetgen.main import BioNetGenTest

tfold = os.path.dirname(__file__)


def test_network_parse():
    netfile = os.path.join(tfold, "mockup.net")
    from bionetgen.network.network import Network

    try:
        net = Network(netfile)
        res = True
    except:
        res = False
    assert res is True


def test_pattern_reader():
    patfile = os.path.join(tfold, "patterns.txt")
    from bionetgen.modelapi.pattern_reader import BNGPatternReader

    try:
        with open(patfile, "r") as f:
            patterns = f.readlines()
            for pattern in patterns:
                pat_obj = BNGPatternReader(pattern).pattern
                reparsed_pat = BNGPatternReader(str(pat_obj)).pattern
                if pat_obj != reparsed_pat:
                    raise RuntimeError(
                        f"Pattern can't be reparsed correctly, og: {pat_obj}, reparsed: {reparsed_pat}"
                    )
        res = True
    except:
        res = False
    assert res is True


def test_pattern_canonicalization():
    # for now, if the platform is windows, just skip
    if os.name == "nt":
        assert True is True
    # if pynauty is uninstalled, skip the test
    try:
        import pynauty
    except ImportError:
        assert True is True
        return
    # otherwise we will test canonicalization
    from bionetgen.modelapi.pattern_reader import BNGPatternReader

    # the testing file
    testfile = os.path.join(tfold, "canon_label_testing.txt")
    with open(testfile, "r+") as f:
        tests = f.readlines()
    # loop over tests
    res = True
    for ipat, pat in enumerate(tests):
        pat_splt = pat.split("    ")
        pat1, pat2 = pat_splt[0], pat_splt[1]
        try:
            # read patterns
            pat1_obj = BNGPatternReader(pat1).pattern
            pat2_obj = BNGPatternReader(pat2).pattern
            # compare them
            if pat1_obj != pat2_obj:
                res = False
                break
        except:
            res = False
            break
    # assert that everything matched up
    assert res is True
