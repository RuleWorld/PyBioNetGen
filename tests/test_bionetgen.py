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


def test_bionetgen_model():
    fpath = os.path.join(tfold, "test.bngl")
    fpath = os.path.abspath(fpath)
    m = bng.bngmodel(fpath)


def test_bionetgen_visualize():
    vis_types = [
        "contactmap",
        "ruleviz_pattern",
        "ruleviz_operation",
        "regulatory",
        "atom_rule",
        "all",
    ]
    for vis_name in vis_types:
        argv = [
            "visualize",
            "-i",
            os.path.join(tfold, "test.bngl"),
            "-o",
            os.path.join(tfold, "viz"),
            "-t",
            vis_name,
        ]
        with BioNetGenTest(argv=argv) as app:
            app.run()
            assert app.exit_code == 0
            # gmls = glob.glob("*.gml")
            graphmls = glob.glob(os.path.join(tfold, "viz") + os.sep + "*.graphml")
            if vis_name == "atom_rule":
                assert any(["regulatory" in i for i in graphmls])
            elif not vis_name == "all":
                assert any([vis_name in i for i in graphmls])
            else:
                assert len(graphmls) == 4


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


def test_bionetgen_info():
    # tests info subcommand
    argv = ["info"]
    with BioNetGenTest(argv=argv) as app:
        app.run()
        assert app.exit_code == 0


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


def test_atomize_flat():
    if not os.path.exists(os.path.join(tfold, "test")):
        os.mkdir(os.path.join(tfold, "test"))
    argv = [
        "atomize",
        "-i",
        os.path.join(tfold, "test_sbml.xml"),
        "-o",
        os.path.join(*[tfold, "test", "test_sbml_flat.bngl"]),
    ]
    to_match = ["test_sbml_flat.bngl"]
    with BioNetGenTest(argv=argv) as app:
        app.run()
        assert app.exit_code == 0
        file_list = os.listdir(os.path.join(tfold, "test"))
        assert file_list.sort() == to_match.sort()


def test_atomize_atomized():
    if not os.path.exists(os.path.join(tfold, "test")):
        os.mkdir(os.path.join(tfold, "test"))
    argv = [
        "atomize",
        "-i",
        os.path.join(tfold, "test_sbml.xml"),
        "-o",
        os.path.join(*[tfold, "test", "test_sbml_atom.bngl"]),
        "-a",
    ]
    to_match = ["test_sbml_atom.bngl"]
    with BioNetGenTest(argv=argv) as app:
        app.run()
        assert app.exit_code == 0
        file_list = os.listdir(os.path.join(tfold, "test"))
        assert file_list.sort() == to_match.sort()


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


# def test_graphdiff_matrix():
#     valid = []
#     invalid = []
#     argv = [
#         "graphdiff",
#         "-i",
#         os.path.join(*[tfold, "models", "testviz1_cm.graphml"]),
#         "-i2",
#         os.path.join(*[tfold, "models", "testviz2_cm.graphml"]),
#         "-m",
#         "matrix",
#     ]
#     to_validate = ["testviz1_cm_recolored.graphml",
#                 "testviz1_cm_testviz2_cm_diff.graphml",
#                 "testviz2_cm_recolored.graphml",
#                 "testviz2_cm_testviz1_cm_diff.graphml",
#                 ]
#     schema_doc = etree.parse(f)
#     xmlschema = etree.XMLSchema(schema_doc)

#     with BioNetGenTest(argv=argv) as app:
#         app.run()
#         assert app.exit_code == 0
#     for test_graphml in to_validate:
#         doc = etree.parse(test_graphml)
#         result = xmlschema.validate(doc)
#         if result == True: valid.append(test_graphml)
#         else:
#             invalid.append(test_graphml)
#     print(sorted(valid))
#     print(sorted(invalid))
#     # assert len(valid) == 4


# def test_graphdiff_union():
#     argv = [
#         "graphdiff",
#         "-i",
#         os.path.join(tfold, "models", "testviz1_cm.graphml"),
#         "-i2",
#         os.path.join(tfold, "models", "testviz2_cm.graphml"),
#         "-m",
#         "union",
#     ]
#     to_validate = "testviz1_cm_testviz2_cm_union.graphml"
#     # xmlschema_doc = etree.parse("INSERT_xsd_path_HERE.xsd")
#     # xmlschema = etree.XMLSchema(xmlschema_doc)
#     with BioNetGenTest(argv=argv) as app:
#         app.run()
#         assert app.exit_code == 0
#     # xml_doc = etree.parse(to_validate)
#     # result = xmlschema.validate(xml_doc)
#     # assert result == True
