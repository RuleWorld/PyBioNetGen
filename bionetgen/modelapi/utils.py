from typing import OrderedDict


class Operation:
    """
    Class for rule operations
    """

    # valid operation types
    valid_ops = [
        "AddBond",
        "DeleteBond",
        "ChangeCompartment",
        "StateChange",
        "Add",
        "Delete",
    ]
    valid_args = [
        "@site1",
        "@site2",
        "@id",
        "@source",
        "@destination",
        "@flipOrientation",
        "@moveConnected",
        "@site",
        "@finalState",
        "@DeleteMolecules",
    ]

    def __init__(self, op_type=None) -> None:
        self.type = op_type
        self.args = []

    def __str__(self) -> str:
        opstr = f"Operation of type {self.type}"
        return opstr

    def __repr__(self) -> str:
        return str(self)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, val):
        if val in self.valid_ops or val is None:
            self._type = val
        else:
            print(f"Operation type {val} is not a valid operation type")


class RuleMod:
    """
    Rule modifiers class for storage and printing.
    """

    def __init__(self, mod_type=None) -> None:
        # valid mod types
        self.valid_mod_names = ["DeleteMolecules", "MoveConnected", "TotalRate"]
        self.type = mod_type

    def __str__(self) -> str:
        if self.type is None:
            return ""
        else:
            return self.type

    def __repr__(self) -> str:
        return f"Rule modifier of type {self.type}"

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, val):
        if val in self.valid_mod_names or val is None:
            self._type = val
        else:
            print(f"Rule modifier type {val} is not a valid type")
