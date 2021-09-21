import bionetgen as bng
import os, re

from bionetgen.main import BioNetGen
from .utils import find_BNG_path, run_command, ActionList
from tempfile import TemporaryDirectory

# This allows access to the CLIs config setup
app = BioNetGen()
app.setup()
conf = app.config["bionetgen"]
def_bng_path = conf["bngpath"]


class BNGFile:
    """
    File object designed to deal with .bngl file manipulations.

    Usage: BNGFile(bngl_path)
           BNGFile(bngl_path, BNGPATH)

    Attributes
    ----------
    path : str
        path to the file the object needs to deal with
    _action_list : list[str]
        list of acceptible actions
    BNGPATH : str
        optional path to bng folder that contains BNG2.pl
    bngexec : str
        path to BNG2.pl

    Methods
    -------
    generate_xml(xml_file, model_file=None) : bool
        takes the given BNGL file and generates a BNG-XML from it
    strip_actions(model_path, folder) : str
        deletes actions from a given BNGL file
    write_xml(open_file, xml_type="bngxml", bngl_str=None) : bool
        given a bngl file or a string, writes an SBML or BNG-XML from it
    """

    def __init__(self, path, BNGPATH=def_bng_path) -> None:
        self.path = path
        AList = ActionList()
        self._action_list = [i + "(" for i in AList.possible_types]
        BNGPATH, bngexec = find_BNG_path(BNGPATH)
        self.BNGPATH = BNGPATH
        self.bngexec = bngexec
        self.parsed_actions = []

    def generate_xml(self, xml_file, model_file=None) -> bool:
        """
        generates an BNG-XML file from a given model file. Defaults
        to self.path if model_file is not given
        """
        if model_file is None:
            model_file = self.path
        cur_dir = os.getcwd()
        # temporary folder to work in
        with TemporaryDirectory() as temp_folder:
            # make a stripped copy without actions in the folder
            stripped_bngl = self.strip_actions(model_file, temp_folder)
            # run with --xml
            os.chdir(temp_folder)
            # TODO: take stdout option from app instead
            rc, _ = run_command(["perl", self.bngexec, "--xml", stripped_bngl])
            if rc == 1:
                # if we fail, print out what we have to
                # let the user know what BNG2.pl says
                # if rc.stdout is not None:
                #     print(rc.stdout.decode('utf-8'))
                # if rc.stderr is not None:
                #     print(rc.stderr.decode('utf-8'))
                # go back to our original location
                os.chdir(cur_dir)
                # shutil.rmtree(temp_folder)
                return False
            else:
                # we should now have the XML file
                path, model_name = os.path.split(stripped_bngl)
                model_name = model_name.replace(".bngl", "")
                written_xml_file = model_name + ".xml"
                with open(written_xml_file, "r") as f:
                    content = f.read()
                    xml_file.write(content)
                # since this is an open file, to read it later
                # we need to go back to the beginning
                xml_file.seek(0)
                # go back to our original location
                os.chdir(cur_dir)
                return True

    def strip_actions(self, model_path, folder) -> str:
        """
        Strips actions from a BNGL file and makes a copy
        into the given folder
        """
        # Get model name and setup path stuff
        path, model_file = os.path.split(model_path)
        # open model and strip actions
        with open(model_path, "r", encoding="UTF-8") as mf:
            # read and strip actions
            mstr = mf.read()
            # TODO: Clean this up _a lot_
            # this removes any new line escapes (\ \n) to continue
            # to another line, so we can just remove the action lines
            mstr = re.sub(r"\\\n", "", mstr)
            mlines = mstr.split("\n")
            stripped_lines = list(filter(lambda x: self._not_action(x), mlines))
            # remove spaces, actions don't allow them
            self.parsed_actions = [
                x.replace(" ", "")
                for x in filter(lambda x: not self._not_action(x), mlines)
            ]
            # let's remove begin/end actions, rarely used but should be removed
            remove_from = -1
            remove_to = -1
            for iline, line in enumerate(stripped_lines):
                if re.match(r"\s*(begin)\s+(actions)\s*", line):
                    remove_from = iline
                elif re.match(r"\s*(end)\s+(actions)\s*", line):
                    remove_to = iline
            if remove_from > 0:
                # we have a begin/end actions block
                if remove_to < 0:
                    raise RuntimeError(
                        f'There is a "begin actions" statement at line {remove_from} without a matching "end actions" statement'
                    )
                stripped_lines = (
                    stripped_lines[:remove_from] + stripped_lines[remove_to + 1 :]
                )
            if remove_to > 0:
                if remove_from < 0:
                    raise RuntimeError(
                        f'There is an "end actions" statement at line {remove_to} without a matching "begin actions" statement'
                    )
        # TODO: read stripped lines and store the actions
        # open new file and write just the model
        stripped_model = os.path.join(folder, model_file)
        stripped_lines = [x + "\n" for x in stripped_lines]
        with open(stripped_model, "w") as sf:
            sf.writelines(stripped_lines)
        return stripped_model

    def _not_action(self, line) -> bool:
        for action in self._action_list:
            if action in line:
                return False
        return True

    def write_xml(self, open_file, xml_type="bngxml", bngl_str=None) -> bool:
        """
        write new BNG-XML or SBML of file by calling BNG2.pl again
        or can take BNGL string in as well.
        """
        # TODO: Implement the route where this function uses the file itself
        # for this generation
        if bngl_str is None:
            # should load in the right str here
            raise NotImplementedError

        cur_dir = os.getcwd()
        # temporary folder to work in
        with TemporaryDirectory() as temp_folder:
            # write the current model to temp folder
            os.chdir(temp_folder)
            with open("temp.bngl", "w") as f:
                f.write(bngl_str)
            # run with --xml
            # TODO: Make output supression an option somewhere
            if xml_type == "bngxml":
                rc, _ = run_command(["perl", self.bngexec, "--xml", "temp.bngl"])
                if rc == 1:
                    print("XML generation failed")
                    # go back to our original location
                    os.chdir(cur_dir)
                    return False
                else:
                    # we should now have the XML file
                    with open("temp.xml", "r") as f:
                        content = f.read()
                        open_file.write(content)
                    # go back to beginning
                    open_file.seek(0)
                    os.chdir(cur_dir)
                    return True
            elif xml_type == "sbml":
                command = ["perl", self.bngexec, "temp.bngl"]
                rc, _ = run_command(command)
                if rc == 1:
                    print("SBML generation failed")
                    # go back to our original location
                    os.chdir(cur_dir)
                    return False
                else:
                    # we should now have the SBML file
                    with open("temp_sbml.xml", "r") as f:
                        content = f.read()
                        open_file.write(content)
                    open_file.seek(0)
                    os.chdir(cur_dir)
                    return True
            else:
                print("XML type {} not recognized".format(xml_type))
                return False
