import os, glob
from pytest import raises
import bionetgen as bng
from bionetgen.main import BioNetGenTest

tfold = os.path.dirname(__file__)


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
