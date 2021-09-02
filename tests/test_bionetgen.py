import os, glob
import shutil
from pytest import raises
import bionetgen as bng
from bionetgen.main import BioNetGenTest

tfold = os.path.dirname(__file__)


# def test_bionetgen_help():
#     # test basic command help
#     with raises(SystemExit):
#         argv = ["--help"]
#         with BioNetGenTest(argv=argv) as app:
#             app.run()
#             assert app.exit_code == 0


# def test_bionetgen_input():
#     # test basic command help
#     argv = ["run", "-i", "test.bngl", "-o", os.path.join(tfold, "test")]
#     to_match = ["test.xml", "test.cdat", "test.gdat", "test.net"]
#     with BioNetGenTest(argv=argv) as app:
#         app.run()
#         assert app.exit_code == 0
#         file_list = os.listdir(os.path.join(tfold, "test"))
#         assert file_list.sort() == to_match.sort()


# def test_bionetgen_model():
#     fpath = os.path.join(tfold, "test.bngl")
#     fpath = os.path.abspath(fpath)
#     m = bng.bngmodel(fpath)


# def test_bionetgen_all_model_loading():
#     mpattern = os.path.join(tfold, "models") + os.sep + "*.bngl"
#     models = glob.glob(mpattern)
#     succ = []
#     fail = []
#     success = 0
#     fails = 0
#     for model in models:
#         try:
#             m = bng.bngmodel(model)
#             success += 1
#             mstr = str(m)
#             succ.append(model)
#         except:
#             print("can't load model {}".format(model))
#             fails += 1
#             fail.append(model)
#     print("succ: {}".format(success))
#     # print(sorted(succ))
#     print("fail: {}".format(fails))
#     print(sorted(fail))
#     assert fails == 0


# def test_action_loading():
#     all_action_model = os.path.join(*[tfold, "models", "all_actions.bngl"])
#     m = bng.bngmodel(all_action_model)
#     assert len(m.actions) == 27


# def test_bionetgen_info():
#     # test info subcommand
#     argv = ["info"]
#     with BioNetGenTest(argv=argv) as app:
#         app.run()
#         assert app.exit_code == 0


# def test_model_running_CLI():
#     # test running a few models using the CLI
#     models = ["test_MM.bngl", "motor.bngl", "simple_system.bngl"]
#     succ = []
#     fail = []
#     success = 0
#     fails = 0
#     for model in models:
#         fpath = os.path.join(*[tfold, "models", model])
#         fpath = os.path.abspath(fpath)
#         try:
#             fpath = os.path.join(*[tfold, "models", model])
#             fpath = os.path.abspath(fpath)
#             argv = ["run", "-i", fpath, "-o", "cli_test_runs"]
#             with BioNetGenTest(argv=argv) as app:
#                 app.run()
#                 assert app.exit_code == 0
#             success += 1
#             succ.append(model)
#         except:
#             print("can't run model {}".format(model))
#             fails += 1
#             fail.append(model)
#     del model, fpath
#     print("succ: {}".format(success))
#     print(sorted(succ))
#     print("fail: {}".format(fails))
#     print(sorted(fail))
#     assert fails == 0


def test_model_running_lib():
    # test running a few models using the library
    # models = ["test_MM.bngl", "motor.bngl", "simple_system.bngl"]
    models = ["test_MM.bngl"]
    succ = []
    fail = []
    success = 0
    fails = 0
    for model in models:
        fpath = os.path.join(*[tfold, "models", model])
        fpath = os.path.abspath(fpath)
        try:
            # result = bng.run(fpath, out="lib_test_runs")
            # ONLY works if out folder is specified -- WHY?
            # seems like an issue with try-except - works fine in separate .ipynb
            bng.run(fpath)
            success += 1
            succ.append(model)
        except:
            print("can't run model {}".format(model))
            fails += 1
            fail.append(model)
    del model, fpath
    print("succ: {}".format(success))
    print(sorted(succ))
    print("fail: {}".format(fails))
    print(sorted(fail))
    assert fails == 0
