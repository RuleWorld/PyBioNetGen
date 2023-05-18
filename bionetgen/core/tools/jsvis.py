import bionetgen, json

from bionetgen.core.utils.logging import BNGLogger


class BNGJSVisualize:
    def __init__(
        self, input_file, output=None, bngpath=None, suppress=None, app=None
    ) -> None:
        self.app = app
        self.logger = BNGLogger(app=self.app)
        self.logger.debug(
            "Setting up BNGJSVisualize object",
            loc=f"{__file__} : BNGJSVisualize.__init__()",
        )
        # set input, required
        self.input = input_file
        # set output
        self.output = output
        self.suppress = suppress
        self.bngpath = bngpath

    def run(self):
        self.logger.debug("Running", loc=f"{__file__} : BNGJSVisualize.run()")
        return self._normal_mode()

    def _normal_mode(self):
        self.logger.debug(
            f"Running on normal mode, loading model {self.input}",
            loc=f"{__file__} : BNGJSVisualize._normal_mode()",
        )
        model = bionetgen.modelapi.bngmodel(self.input)
        model.actions.clear_actions()
        # setup settings dictionary to write as JSON
        settings = {}
        settings["visualization_settings"] = {}
        settings["visualization_settings"]["general"] = {}
        settings["visualization_settings"]["general"]["width"] = None
        settings["visualization_settings"]["general"]["height"] = None
        # add model here
        settings["visualization_settings"]["model"] = model.xml_dict
        # build SVGs here
        svgs = {}
        # we need to update the XML and build SVGs at the same time
        mtypes = model.xml_dict["sbml"]["model"]["ListOfMoleculeTypes"]["MoleculeType"]
        if isinstance(mtypes, list):
            for imtype, mtype in enumerate(mtypes):
                self.parse_molec(mtype, svgs)
        else:
            self.parse_molec(mtypes, svgs)
        settings["visualization_settings"]["svgs"] = list(svgs.values())
        # write the settings JSON
        with open(self.output, "w+") as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def parse_state(self, state_dict):
        state_name = state_dict["@id"]
        # make state SVG
        state_svg = {
            "name": state_name,
            "type": "string",
            "string": '<svg height="500" width="500"><circle cx="100" cy="100" r="100" stroke="black" stroke-width="3" fill="black" /></svg>',  # this is the state SVG string
        }
        return state_svg

    def parse_comp(self, comp_dict, svgs):
        states = comp_dict["ListOfAllowedStates"]["AllowedState"]
        if isinstance(states, list):
            for istate, state in enumerate(states):
                state_name = state["@id"]
                state["svg_name"] = state_name
                svgs[state_name] = self.parse_state(state)
        else:
            state_name = states["@id"]
            states["svg_name"] = state_name
            svgs[state_name] = self.parse_state(states)

    def parse_molec(self, molec_dict, svgs):
        molec_name = molec_dict["@id"]
        # make molecule SVG
        molec_svg = {
            "name": molec_name,
            "type": "string",
            "string": '<svg width="200" height="200"><rect width="200" height="200" style="fill:rgb(0,0,0);stroke-width:3;stroke:rgb(0,0,0)"/></svg>',  # this is the molecule SVG string
        }
        molec_dict["svg_name"] = molec_name
        svgs[molec_name] = molec_svg
        if "ListOfComponentTypes" in molec_dict:
            comps = molec_dict["ListOfComponentTypes"]["ComponentType"]
            if isinstance(comps, list):
                for icomp, comp in enumerate(comps):
                    if "ListOfAllowedStates" in comp:
                        self.parse_comp(comp, svgs)
            else:
                if "ListOfAllowedStates" in comps:
                    self.parse_comp(comps, svgs)
