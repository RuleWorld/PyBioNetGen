import os, glob
from pytest import raises
import bionetgen as bng
from bionetgen.main import BioNetGenTest

tfold = os.path.dirname(__file__)


def test_bionetgen_help():
    # tests basic command help
    with raises(SystemExit):
        argv = ["--help"]
        with BioNetGenTest(argv=argv) as app:
            app.run()
            assert app.exit_code == 0


def test_bionetgen_input():
    argv = [
        "run",
        "-i",
        os.path.join(tfold, "test.bngl"),
        "-o",
        os.path.join(tfold, "test"),
    ]
    to_match = ["test.xml", "test.cdat", "test.gdat", "test.net"]
    with BioNetGenTest(argv=argv) as app:
        app.run()
        assert app.exit_code == 0
        file_list = os.listdir(os.path.join(tfold, "test"))
        assert file_list.sort() == to_match.sort()


def test_bionetgen_plot():
    argv = [
        "plot",
        "-i",
        os.path.join(*[tfold, "test", "test.gdat"]),
        "-o",
        os.path.join(*[tfold, "test", "test.png"]),
    ]
    with BioNetGenTest(argv=argv) as app:
        app.run()
        assert app.exit_code == 0
        assert os.path.isfile(os.path.join(*[tfold, "test", "test.png"]))


def test_bionetgen_info():
    # tests info subcommand
    argv = ["info"]
    with BioNetGenTest(argv=argv) as app:
        app.run()
        assert app.exit_code == 0
