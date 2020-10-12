import os
from pytest import raises
from bionetgen.main import BioNetGenTest

def test_bionetgen_help():
    # test basic command help
    with raises(SystemExit):
        argv = ['--help']
        with BioNetGenTest(argv=argv) as app:
            app.run()
            assert app.exit_code == 0

def test_bionetgen_input(tmp):
    # test basic command help
    argv = ['-i', 'test.bngl', '-o', tmp.dir]
    to_match = ['test.xml', 'test.cdat', 'test.gdat', 'test.net']
    with BioNetGenTest(argv=argv) as app:
        app.run()
        assert app.exit_code == 0
        file_list = os.listdir(tmp.dir)
        assert file_list.sort() == to_match.sort()
