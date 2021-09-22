import os, bionetgen, glob
from tempfile import TemporaryDirectory


class VisResult:
    def __init__(self, input_folder, name=None, vtype=None) -> None:
        self.input_folder = input_folder
        self.name = name
        self.vtype = vtype
        self.rc = None
        self.out = None
        self.files = []
        self.file_strs = {}
        self.file_graphs = {}
        self._load_files()

    def _load_files(self) -> None:
        # we need to assume some sort of GML output
        # at least for now
        # use the name, if given, search for GMLs if not
        gmls = glob.glob("*.gml")
        for gml in gmls:
            if self.name is None:
                self.files.append(gml)
                # now load into string
                with open(gml, "r") as f:
                    l = f.read()
                self.file_strs[gml] = l
            else:
                # pull GMLs that contain the name
                if self.name in gml:
                    self.files.append(gml)
                    # now load into string
                    with open(gml, "r") as f:
                        l = f.read()
                    self.file_strs[gml] = l

    def _dump_files(self, folder) -> None:
        os.chdir(folder)
        for gml in self.files:
            gml_name = os.path.split(gml)[-1]
            with open(gml_name, "w") as f:
                f.write(self.file_strs[gml])


class BNGVisualize:
    def __init__(
        self, input_file, output=None, vtype=None, bngpath=None, suppress=None
    ) -> None:
        # set input, required
        self.input = input_file
        # set valid types
        self.valid_types = [
            "contactmap",
            "ruleviz_pattern",
            "ruleviz_operation",
            "regulatory",
        ]
        # set visualization type, default yo contactmap
        if vtype is None or len(vtype) == 0:
            vtype = "contactmap"
        if vtype not in self.valid_types:
            raise ValueError(f"{vtype} is not a valid visualization type")
        self.vtype = vtype
        # set output
        self.output = output
        self.suppress = suppress
        self.bngpath = bngpath

    def run(self) -> VisResult:
        model = bionetgen.modelapi.bngmodel(self.input)
        model.actions.clear_actions()
        model.add_action("visualize", action_args={"type": f"'{self.vtype}'"})
        # TODO: Work in temp folder
        cur_dir = os.getcwd()
        from bionetgen.core.main import BNGCLI

        if self.output is None:
            with TemporaryDirectory() as out:
                # instantiate a CLI object with the info
                cli = BNGCLI(model, out, self.bngpath, suppress=self.suppress)
                try:
                    cli.run()
                    # load vis
                    vis_res = VisResult(
                        os.path.abspath(os.getcwd()),
                        name=model.model_name,
                        vtype=self.vtype,
                    )
                    # go back
                    os.chdir(cur_dir)
                    # dump files
                    vis_res._dump_files(cur_dir)
                    return vis_res
                except Exception as e:
                    os.chdir(cur_dir)
                    # TODO: Better error reporting, improve consistency of reporting
                    print("Couldn't run the simulation")
                    print(e)
                    raise
        else:
            # instantiate a CLI object with the info
            cli = BNGCLI(model, self.output, self.bngpath, suppress=self.suppress)
            try:
                cli.run()
                # load vis
                vis_res = VisResult(
                    os.path.abspath(os.getcwd()),
                    name=model.model_name,
                    vtype=self.vtype,
                )
                # go back
                os.chdir(cur_dir)
                # dump files
                vis_res._dump_files(cur_dir)
                return vis_res
            except Exception as e:
                os.chdir(cur_dir)
                # TODO: Better error reporting, improve consistency of reporting
                print("Couldn't run the simulation")
                print(e)
                raise
