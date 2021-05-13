from .structs import Parameter

class BaseLine:
    '''
    Base line object

    Attributes
    ----------
    line_label
    comment 
    content
    _recompile : boolean
        a tag to keep track if something is changed in the block. this
        will be used in the future to recompile a simulator whne something
        is changed
    _changes : Dict
        a dictionary to keep track of any changes to any items that are in
        a block. this can be used to just keep a history but it can also be
        useful for model validity later


    Methods
    -------
    '''
    def __init__(self) -> str:
        self._line_label = None
        self._comment = None
        self.content = None
        self._recompile = False
        self._changes = {}

    def __repr__(self) -> str:
        return self.gen_string()

    def __str__(self) -> str:
        return self.gen_string()

    def __iter__(self):
        return self.content.__iter__()
    
    def __contains__(self, key):
        return key in self.content
    
    def __getitem__(self, key):
        return self.content[key]

    def __setitem__(self, key, value):
        self.content[key] = value

    def __delitem__(self, key):
        self.content.__delitem__[key]

    @property
    def comment(self) -> None:
        return self._comment
        
    @comment.setter
    def comment(self, val) -> str:
        # TODO: regex handling of # instead
        if val.startswith("#"):
            self._comment = val[1:]
        else:
            self._comment = val
    
    @property
    def line_label(self) -> str:
        return self._line_label
    
    @line_label.setter
    def line_label(self, val) -> None:
        # TODO: specific error handling
        try:
            ll = int(val)
            self._line_label = "{} ".format(ll)
        except:
            self._line_label = "{}: ".format(val)

    def gen_string(self) -> str:
        # let's deal with line label
        if self.line_label is not None:
            s = self.line_label
        # start building the rest of the string
        s += str(self.content)
        if self.comment is not None:
            s += " #{}".format(self.comment)
        return s


class ParameterLine(BaseLine):
    def __init__(self):
        super().__init__()
    
    def set_parameter(self, name, value, expr=None):
        self.content = Parameter(name, value, expr)

  
class CompartmentLine(BaseLine):
    def __init__(self):
        super().__init__()


class ObservableLine(BaseLine):
    '''
    Observable line object. 

    Attributes
    ----------
    patterns : list
        list of Pattern objects that make up the observable
    '''
    def __init__(self):
        super().__init__()


class SpeciesLine(BaseLine):
    '''
    Species line object.

    Attributes
    ----------

    '''
    def __init__(self):
        super().__init__()


class MolTypeLine(BaseLine):
    '''
    Molecule Type line object.

    Attributes
    ----------
    

    Methods
    -------

    '''
    def __init__(self):
        super().__init__()


class FunctionLine(BaseLine):
    # TODO for some reason the resolve_xml doesn't set the full
    # function string and it's also not used downstream. 

    '''
    Function line object.

    Attributes
    ----------

    
    Methods
    -------

    '''
    def __init__(self):
        super().__init__()


class RuleLine(BaseLine):
    '''
    Rule line object.


    Attributes
    ----------

    Methods
    -------

    '''
    def __init__(self):
        super().__init__()


class ActionLine(BaseLine):
    '''
    Action line object.


    Attributes
    ----------

    Methods
    -------

    '''
    # TODO: Action line doesn't have a line label
    def __init__(self):
        super().__init__()