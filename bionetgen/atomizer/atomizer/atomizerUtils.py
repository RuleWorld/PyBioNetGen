class BindingException(Exception):
    def __init__(self, value, combinations):
        self.value = value
        self.combinations = combinations

    def __str__(self):
        return repr(self.value)
