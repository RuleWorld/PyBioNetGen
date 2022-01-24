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
        return f"Rule modifier of tyoe {self.type}"

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, val):
        if val in self.valid_mod_names or val is None:
            self._type = val
        else:
            print(f"Rule modifier type {val} is not a valid type")
