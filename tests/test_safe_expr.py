"""Parameter expressions from model files must not be evaluated as Python (issue #118)."""

import pytest

import bionetgen
from bionetgen.core.utils.safe_expr import fold_numeric, is_safe_expression

POC_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sbml xmlns="http://www.sbml.org/sbml/level3" level="3" version="1">
  <model id="toy">
    <ListOfParameters>
      <Parameter id="k1" type="Constant" value="1"
                 expr="{expr}"/>
    </ListOfParameters>
  </model>
</sbml>
"""


def _payload(marker):
    # open(...).write(...) creates the marker file if the expression is ever evaluated.
    return "open(&apos;{}&apos;, &apos;w&apos;).write(&apos;x&apos;) or 1".format(
        marker
    )


def test_xml_parameter_expression_is_not_executed(tmp_path):
    marker = tmp_path / "executed.txt"
    model_file = tmp_path / "evil_model.xml"
    model_file.write_text(POC_XML.format(expr=_payload(marker)))

    model = bionetgen.bngmodel(str(model_file))

    assert not marker.exists()
    assert model.model_name == "toy"


def test_import_payload_is_not_executed(tmp_path):
    marker = tmp_path / "executed.txt"
    expr = "__import__('os').system('touch {}') or 1".format(marker)
    assert fold_numeric(expr) == expr
    assert not marker.exists()


def test_xml_constant_expression_still_folds(tmp_path):
    model_file = tmp_path / "ok_model.xml"
    model_file.write_text(POC_XML.format(expr="2*3"))
    model = bionetgen.bngmodel(str(model_file))
    assert float(model.parameters.k1.value) == 6.0


@pytest.mark.parametrize(
    "text, expected",
    [
        ("2*3", "6.0"),
        ("2^3", "8.0"),
        ("1e-3", "0.001"),
        ("-(4+2)/3", "-2.0"),
        ("exp(0)", "1.0"),
        ("sqrt(16)", "4.0"),
        ("k1*2", "k1*2"),
        ("NA*V", "NA*V"),
    ],
)
def test_fold_numeric_arithmetic(text, expected):
    assert fold_numeric(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "__import__('os').system('id')",
        "open('x', 'w')",
        "().__class__.__bases__",
        "exp.__globals__",
        "[1, 2]",
        "lambda: 1",
        "_hidden + 1",
        "exp(x=1)",
        "'a string'",
        "1" * 2000,
    ],
)
def test_unsafe_or_non_arithmetic_is_left_as_text(text):
    assert not is_safe_expression(text)
    assert fold_numeric(text) == text
