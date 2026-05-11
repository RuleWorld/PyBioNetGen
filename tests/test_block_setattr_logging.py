"""Focused tests for block setattr logging and helper deduplication."""

from collections import OrderedDict
from unittest.mock import patch

import pytest

from bionetgen.modelapi.blocks import (
    CompartmentBlock,
    EnergyPatternBlock,
    FunctionBlock,
    MoleculeTypeBlock,
    ObservableBlock,
    ParameterBlock,
    PopulationMapBlock,
    RuleBlock,
    SpeciesBlock,
)
from bionetgen.modelapi.structs import Action, Rule, Species
from bionetgen.network.blocks import (
    NetworkCompartmentBlock,
    NetworkEnergyPatternBlock,
    NetworkFunctionBlock,
    NetworkGroupBlock,
    NetworkParameterBlock,
    NetworkPopulationMapBlock,
    NetworkReactionBlock,
    NetworkSpeciesBlock,
)
from bionetgen.network.structs import NetworkReaction, NetworkSpecies


class FakePattern:
    """Minimal mock for Pattern-like objects used by several block items."""

    def __init__(self, name="A()"):
        self.name = name
        self.MatchOnce = False

    def __str__(self):
        return self.name


class DuplicateArgsDict(dict):
    """A dict subclass whose items() preserves duplicate logical arguments."""

    def items(self):
        return [("method", '"ssa"'), ("method", '"ode"')]


def _make_parameter_block():
    block = ParameterBlock()
    block.add_parameter("k1", 0.5)
    block._changes.clear()
    return block, "k1", block["k1"]


def _make_compartment_block():
    block = CompartmentBlock()
    block.add_compartment("EC", 3, 1.0)
    block._changes.clear()
    return block, "EC", block["EC"]


def _make_observable_block():
    block = ObservableBlock()
    block.add_observable("obsA", "Molecules", [FakePattern("A()")])
    block._changes.clear()
    return block, "obsA", block["obsA"]


def _make_species_block():
    block = SpeciesBlock()
    block.items["A()"] = Species(pattern=FakePattern("A()"), count=100)
    block._changes.clear()
    return block, "A()", block["A()"]


def _make_molecule_type_block():
    block = MoleculeTypeBlock()
    block.add_molecule_type("A", [])
    block._changes.clear()
    return block, "A", block["A"]


def _make_function_block():
    block = FunctionBlock()
    block.add_function("f1", "k1*A")
    block._changes.clear()
    return block, "f1", block["f1"]


def _make_rule_block():
    block = RuleBlock()
    pattern = FakePattern("A()")
    block.add_rule(
        "r1", reactants=[pattern], products=[pattern], rate_constants=("k1",)
    )
    block._changes.clear()
    return block, "r1", block["r1"]


def _make_energy_pattern_block():
    block = EnergyPatternBlock()
    block.add_energy_pattern("ep0", "A()", "E0")
    block._changes.clear()
    return block, "ep0", block["ep0"]


def _make_population_map_block():
    block = PopulationMapBlock()
    block.add_population_map("pm0", "A()", "A_pop", "lump0")
    block._changes.clear()
    return block, "pm0", block["pm0"]


def _make_network_parameter_block():
    block = NetworkParameterBlock()
    block.add_parameter(1, "k1", "0.5")
    block._changes.clear()
    return block, "k1", block["k1"]


def _make_network_compartment_block():
    block = NetworkCompartmentBlock()
    block.add_compartment("cytoplasm", 3, "1.0")
    block._changes.clear()
    return block, "cytoplasm", block["cytoplasm"]


def _make_network_group_block():
    block = NetworkGroupBlock()
    block.add_group(1, "Atot", members=["1"])
    block._changes.clear()
    return block, "Atot", block["Atot"]


def _make_network_species_block():
    block = NetworkSpeciesBlock()
    block.items["A(b)"] = NetworkSpecies(1, "A(b)", count=100)
    block._changes.clear()
    return block, "A(b)", block["A(b)"]


def _make_network_function_block():
    block = NetworkFunctionBlock()
    block.add_function("rate", "k1*A")
    block._changes.clear()
    return block, "rate", block["rate"]


def _make_network_reaction_block():
    block = NetworkReactionBlock()
    block.items["rxn1"] = NetworkReaction(
        1, reactants=["1"], products=["2"], rate_constant="k1"
    )
    block._changes.clear()
    return block, "rxn1", block.items["rxn1"]


def _make_network_energy_pattern_block():
    block = NetworkEnergyPatternBlock()
    block.add_energy_pattern("ep1", "A(b!1).B(a!1)", "epsilon")
    block._changes.clear()
    return block, "ep1", block["ep1"]


def _make_network_population_map_block():
    block = NetworkPopulationMapBlock()
    block.add_population_map("pm1", "A(b~0)", "A_pop", "lump1")
    block._changes.clear()
    return block, "pm1", block["pm1"]


MODEL_CASES = [
    (
        _make_parameter_block,
        object(),
        "Unable to set parameter 'k1'",
        "keeping existing parameter",
        "ParameterBlock.__setattr__()",
    ),
    (
        _make_compartment_block,
        object(),
        "Unable to set compartment 'EC'",
        "keeping existing compartment",
        "CompartmentBlock.__setattr__()",
    ),
    (
        _make_observable_block,
        42,
        "Unable to set observable 'obsA'",
        "keeping existing observable",
        "ObservableBlock.__setattr__()",
    ),
    (
        _make_species_block,
        42,
        "Unable to set species 'A()'",
        "keeping existing species",
        "SpeciesBlock.__setattr__()",
    ),
    (
        _make_molecule_type_block,
        42,
        "Unable to set molecule type 'A'",
        "keeping existing molecule type",
        "MoleculeTypeBlock.__setattr__()",
    ),
    (
        _make_function_block,
        42,
        "Unable to set function 'f1'",
        "keeping existing function",
        "FunctionBlock.__setattr__()",
    ),
    (
        _make_rule_block,
        42,
        "Unable to set rule 'r1'",
        "keeping existing rule",
        "RuleBlock.__setattr__()",
    ),
    (
        _make_energy_pattern_block,
        42,
        "Unable to set energy pattern 'ep0'",
        "keeping existing energy pattern",
        "EnergyPatternBlock.__setattr__()",
    ),
    (
        _make_population_map_block,
        42,
        "Unable to set population map 'pm0'",
        "keeping existing population map",
        "PopulationMapBlock.__setattr__()",
    ),
]


NETWORK_CASES = [
    (
        _make_network_parameter_block,
        object(),
        "Unable to set parameter 'k1'",
        "keeping existing parameter",
        "NetworkParameterBlock.__setattr__()",
    ),
    (
        _make_network_compartment_block,
        object(),
        "Unable to set compartment 'cytoplasm'",
        "keeping existing compartment",
        "NetworkCompartmentBlock.__setattr__()",
    ),
    (
        _make_network_group_block,
        42,
        "Unable to set group 'Atot'",
        "keeping existing group",
        "NetworkGroupBlock.__setattr__()",
    ),
    (
        _make_network_species_block,
        42,
        "Unable to set species 'A(b)'",
        "keeping existing species",
        "NetworkSpeciesBlock.__setattr__()",
    ),
    (
        _make_network_function_block,
        42,
        "Unable to set function 'rate'",
        "keeping existing function",
        "NetworkFunctionBlock.__setattr__()",
    ),
    (
        _make_network_reaction_block,
        42,
        "Unable to set reaction 1",
        "keeping existing reaction",
        "NetworkReactionBlock.__setattr__()",
    ),
    (
        _make_network_energy_pattern_block,
        42,
        "Unable to set energy pattern 'ep1'",
        "keeping existing energy pattern",
        "NetworkEnergyPatternBlock.__setattr__()",
    ),
    (
        _make_network_population_map_block,
        42,
        "Unable to set population map 'pm1'",
        "keeping existing population map",
        "NetworkPopulationMapBlock.__setattr__()",
    ),
]


@pytest.mark.parametrize(
    ("factory", "invalid_value", "message_fragment", "keep_fragment", "loc_fragment"),
    MODEL_CASES,
)
def test_model_block_setattr_invalid_type_logs_warning(
    factory, invalid_value, message_fragment, keep_fragment, loc_fragment
):
    from bionetgen.modelapi import blocks as blocks_module

    block, attr_name, existing_item = factory()

    with patch.object(blocks_module, "logger") as mock_logger:
        setattr(block, attr_name, invalid_value)

    mock_logger.warning.assert_called_once()
    warning_args, warning_kwargs = mock_logger.warning.call_args
    assert message_fragment in warning_args[0]
    assert keep_fragment in warning_args[0]
    assert loc_fragment in warning_kwargs["loc"]
    if isinstance(block._changes, OrderedDict):
        assert len(block._changes) == 0
    assert block.items[attr_name] is existing_item


@pytest.mark.parametrize(
    ("factory", "invalid_value", "message_fragment", "keep_fragment", "loc_fragment"),
    NETWORK_CASES,
)
def test_network_block_setattr_invalid_type_logs_warning(
    factory, invalid_value, message_fragment, keep_fragment, loc_fragment
):
    from bionetgen.network import blocks as blocks_module

    block, attr_name, existing_item = factory()

    with patch.object(blocks_module, "logger") as mock_logger:
        setattr(block, attr_name, invalid_value)

    mock_logger.warning.assert_called_once()
    warning_args, warning_kwargs = mock_logger.warning.call_args
    assert message_fragment in warning_args[0]
    assert keep_fragment in warning_args[0]
    assert loc_fragment in warning_kwargs["loc"]
    assert len(block._changes) == 0
    assert block.items[attr_name] is existing_item


def test_action_duplicate_args_logs_warning():
    from bionetgen.modelapi import structs as structs_module

    with patch.object(structs_module, "logger") as mock_logger:
        action = Action(
            action_type="simulate", action_args=DuplicateArgsDict({"method": '"ode"'})
        )

    mock_logger.warning.assert_called_once()
    warning_args, warning_kwargs = mock_logger.warning.call_args
    assert "argument method already given" in warning_args[0]
    assert 'latter value "ode"' in warning_args[0]
    assert "Action.__init__()" in warning_kwargs["loc"]
    assert action.type == "simulate"
