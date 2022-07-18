import os, glob
from pytest import raises
import bionetgen as bng
from bionetgen.main import BioNetGenTest

tfold = os.path.dirname(__file__)


def test_bionetgen_model():
    fpath = os.path.join(tfold, "test.bngl")
    fpath = os.path.abspath(fpath)
    m = bng.bngmodel(fpath)


def test_bionetgen_all_model_loading():
    # tests library model loading using many models
    mpattern = os.path.join(tfold, "models") + os.sep + "*.bngl"
    models = glob.glob(mpattern)
    succ = []
    fail = []
    success = 0
    fails = 0
    for model in models:
        try:
            m = bng.bngmodel(model)
            success += 1
            mstr = str(m)
            succ.append(model)
        except:
            print("can't load model {}".format(model))
            fails += 1
            fail.append(model)
    print("succ: {}".format(success))
    print(sorted(succ))
    print("fail: {}".format(fails))
    print(sorted(fail))
    assert fails == 0


def test_action_loading():
    # tests a BNGL file containing all BNG actions
    all_action_model = os.path.join(*[tfold, "models", "actions", "all_actions.bngl"])
    m1 = bng.bngmodel(all_action_model)
    assert len(m1.actions) + len(m1.actions.before_model) == 31

    no_action_model = os.path.join(*[tfold, "models", "actions", "no_actions.bngl"])
    m2 = bng.bngmodel(no_action_model)
    assert len(m2.actions) == 0


def test_model_running_CLI():
    # tests running a list of models using the CLI
    mpattern = os.path.join(tfold, "models") + os.sep + "*.bngl"
    models = glob.glob(mpattern)
    succ = []
    fail = []
    success = 0
    fails = 0
    test_run_folder = os.path.join(tfold, "models", "cli_test_runs")
    if not os.path.isdir(test_run_folder):
        os.mkdir(test_run_folder)
    for model in models:
        model_name = os.path.basename(model).replace(".bngl", "")
        try:
            argv = [
                "run",
                "-i",
                model,
                "-o",
                os.path.join(*[tfold, "models", "cli_test_runs", model_name]),
            ]
            with BioNetGenTest(argv=argv) as app:
                app.run()
                assert app.exit_code == 0
            success += 1
            model = os.path.split(model)
            model = model[1]
            succ.append(model)
        except:
            print("can't run model {}".format(model))
            fails += 1
            model = os.path.split(model)
            model = model[1]
            fail.append(model)
    print("succ: {}".format(success))
    print(sorted(succ))
    print("fail: {}".format(fails))
    print(sorted(fail))
    assert fails == 0


def test_model_running_lib():
    # test running a list of models using the library
    mpattern = os.path.join(tfold, "models") + os.sep + "*.bngl"
    models = glob.glob(mpattern)
    succ = []
    fail = []
    success = 0
    fails = 0
    for model in models:
        if "test_tfun" in model:
            continue
        try:
            bng.run(model)
            success += 1
            model = os.path.split(model)
            model = model[1]
            succ.append(model)
        except:
            print("can't run model {}".format(model))
            fails += 1
            model = os.path.split(model)
            model = model[1]
            fail.append(model)
    print("succ: {}".format(success))
    print(sorted(succ))
    print("fail: {}".format(fails))
    print(sorted(fail))
    assert fails == 0


def test_setup_simulator():
    fpath = os.path.join(tfold, "test.bngl")
    fpath = os.path.abspath(fpath)
    try:
        m = bng.bngmodel(fpath)
        librr_simulator = m.setup_simulator()
        res = librr_simulator.simulate(0, 1, 10)
    except:
        res = None
    assert res is not None
