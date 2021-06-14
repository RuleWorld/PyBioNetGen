import re


class BNGNotebook:
    """
    This is a class for writing BNG notebook from a template
    and given arguments.

    Initalize with keywords to replace values in the template.
    E.g. BNGNotebook(template_file, TEST="CHANGE").write(outfile)
    will write the template file to outfile while changing every
    instance of "TEST" to "CHANGE"

    Attributes
    ----------
    template : str
        the notebook template to use
    odict : dict
        the dictionary built from keywords the class is initalized with

    Methods
    -------
    write(outfile)
        writes the template file to outfile, replacing keywords
    """

    def __init__(self, nb_template, **kwargs):
        self.template = nb_template
        self.odict = {}
        for key in kwargs:
            self.odict[key] = kwargs[key]

    def write(self, outfile):
        """
        This method will overwrite the given arguments
        """
        with open(self.template, "r") as f:
            temp_lines = f.readlines()

        new_lines = []
        for line in temp_lines:
            for key in self.odict:
                line = re.sub(key, self.odict[key], line)
            new_lines.append(line)

        with open(outfile, "w") as f:
            f.writelines(new_lines)
