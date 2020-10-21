import re 

class BNGNotebook:
    '''
    This is a class for writing BNG notebook from a template
    and given arguments. 

    Arguments are keyword arguments e.g. INPUT_ARG="replacement"
    '''
    def __init__(self, nb_template, **kwargs):
        self.template = nb_template
        self.odict = {}
        for key in kwargs:
            self.odict[key] = kwargs[key]

    def write(self, outfile):
        '''
        This method will overwrite the given arguments
        '''
        with open(self.template, "r") as f:
            temp_lines = f.readlines()

        new_lines = []
        for line in temp_lines:
            for key in self.odict:
                line = re.sub(key, self.odict[key], line)
            new_lines.append(line)

        with open(outfile, "w") as f:
            f.writelines(new_lines)
