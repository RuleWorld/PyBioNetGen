import os
import subprocess
from distutils import spawn


class ActionList:
    def __init__(self):
        self.normal_types = [
            "generate_network",
            "generate_hybrid_model",
            "simulate",
            "simulate_ode",
            "simulate_ssa",
            "simulate_pla",
            "simulate_nf",
            "parameter_scan",
            "bifurcate",
            "readFile",
            "writeFile",
            "writeModel",
            "writeNetwork",
            "writeXML",
            "writeSBML",
            "writeMfile",
            "writeMexfile",
            "writeMDL",
            "visualize",
        ]
        self.no_setter_syntax = [
            "setConcentration",
            "addConcentration",
            "setParameter",
            "saveParameters",
            "quit",
            "setModelName",
            "substanceUnits",
            "version",
            "setOption",
        ]
        self.square_braces = [
            "saveConcentrations",
            "resetConcentrations",
            "resetParameters",
        ]
        self.before_model = [
            "setModelName",
            "substanceUnits",
            "version",
            "setOption",
        ]
        self.possible_types = (
            self.normal_types + self.no_setter_syntax + self.square_braces
        )
        # Use dictionary to keep track of all possible args (and types?) for each action
        self.arg_dict = {}
        # arg_dict["action"] = ["arg1", "arg2", "etc."]
        # normal_types
        self.arg_dict["generate_network"] = [
            "prefix",
            "suffix",
            "verbose",
            "overwrite",
            "print_iter",
            "max_agg",
            "max_iter",
            "max_stoich",
            "TextReaction",
            "TextSpecies",
        ]
        self.arg_dict["generate_hybrid_model"] = [
            "prefix",
            "suffix",
            "verbose",
            "overwrite",
            "actions",
            "execute",
            "safe",
        ]
        self.arg_dict["simulate"] = [
            "prefix",
            "suffix",
            "verbose",
            "method",
            "argfile",
            "continue",
            "t_start",
            "t_end",
            "n_steps",
            "n_output_steps",
            "sample_times",
            "output_step_interval",
            "max_sim_steps",
            "stop_if",
            "print_on_stop",
            "print_end",
            "print_net",
            "save_progress",
            "print_CDAT",
            "print_functions",
            "netfile",
            "seed",
            # TODO: arguments for a method called "psa" that is not documented in
            # https://docs.google.com/spreadsheets/d/1Co0bPgMmOyAFxbYnGCmwKzoEsY2aUCMtJXQNpQCEUag/
            "poplevel",
            "check_product_scale",
        ]
        self.arg_dict["simulate_ode"] = [
            "prefix",
            "suffix",
            "verbose",
            "argfile",
            "continue",
            "t_start",
            "t_end",
            "n_steps",
            "n_output_steps",
            "sample_times",
            "output_step_interval",
            "max_sim_steps",
            "stop_if",
            "print_on_stop",
            "print_end",
            "print_net",
            "save_progress",
            "print_CDAT",
            "print_functions",
            "netfile",
            "seed",
            "atol",
            "rtol",
            "sparse",
            "steady_state",
        ]
        self.arg_dict["simulate_ssa"] = [
            "prefix",
            "suffix",
            "verbose",
            "argfile",
            "continue",
            "t_start",
            "t_end",
            "n_steps",
            "n_output_steps",
            "sample_times",
            "output_step_interval",
            "max_sim_steps",
            "stop_if",
            "print_on_stop",
            "print_end",
            "print_net",
            "save_progress",
            "print_CDAT",
            "print_functions",
            "netfile",
            "seed",
        ]
        self.arg_dict["simulate_pla"] = [
            "prefix",
            "suffix",
            "verbose",
            "argfile",
            "continue",
            "t_start",
            "t_end",
            "n_steps",
            "n_output_steps",
            "sample_times",
            "output_step_interval",
            "max_sim_steps",
            "stop_if",
            "print_on_stop",
            "print_end",
            "print_net",
            "save_progress",
            "print_CDAT",
            "print_functions",
            "netfile",
            "seed",
            "pla_config",
            "pla_output",
        ]
        self.arg_dict["simulate_nf"] = [
            "prefix",
            "suffix",
            "verbose",
            "argfile",
            "continue",
            "t_start",
            "t_end",
            "n_steps",
            "n_output_steps",
            "sample_times",
            "output_step_interval",
            "max_sim_steps",
            "stop_if",
            "print_on_stop",
            "print_end",
            "print_net",
            "save_progress",
            "print_CDAT",
            "print_functions",
            "netfile",
            "seed",
            "complex",
            "nocslf",
            "notf",
            "binary_output",
            "gml",
            "equil",
            "get_final_state",
            "utl",
            "param",
        ]
        self.arg_dict["simulate"] = list(
            set(
                self.arg_dict["simulate"]
                + self.arg_dict["simulate_ode"]
                + self.arg_dict["simulate_ssa"]
                + self.arg_dict["simulate_pla"]
                + self.arg_dict["simulate_nf"]
            )
        )
        self.arg_dict["parameter_scan"] = [
            "prefix",
            "suffix",
            "verbose",
            "method",
            "argfile",
            "continue",
            "t_start",
            "t_end",
            "n_steps",
            "n_output_steps",
            "sample_times",
            "output_step_interval",
            "max_sim_steps",
            "stop_if",
            "print_on_stop",
            "print_end",
            "print_net",
            "save_progress",
            "print_CDAT",
            "print_functions",
            "netfile",
            "seed",
            "parameter",
            "par_min",
            "par_max",
            "n_scan_pts",
            "log_scale",
            "par_scan_vals",
            "reset_conc",
        ]
        self.arg_dict["parameter_scan"] = list(
            set(self.arg_dict["parameter_scan"] + self.arg_dict["simulate"])
        )
        self.arg_dict["bifurcate"] = [
            "prefix",
            "suffix",
            "verbose",
            "method",
            "argfile",
            "continue",
            "t_start",
            "t_end",
            "n_steps",
            "n_output_steps",
            "sample_times",
            "output_step_interval",
            "max_sim_steps",
            "stop_if",
            "print_on_stop",
            "print_end",
            "print_net",
            "save_progress",
            "print_CDAT",
            "print_functions",
            "netfile",
            "seed",
            "parameter",
            "par_min",
            "par_max",
            "n_scan_pts",
            "log_scale",
            "par_scan_vals",
        ]
        self.arg_dict["bifurcate"] = list(
            set(self.arg_dict["bifurcate"] + self.arg_dict["parameter_scan"])
        )
        self.arg_dict["bifurcate"].remove("reset_conc")
        self.arg_dict["readFile"] = ["file", "blocks", "atomize", "skip_actions"]
        self.arg_dict["writeFile"] = [
            "format",
            "prefix",
            "suffix",
            "evaluate_expressions",
            "include_model",
            "include_network",
            "overwrite",
            "pretty_formatting",
            "TextReaction",
            "TextSpecies",
        ]
        self.arg_dict["writeModel"] = [
            "format",
            "prefix",
            "suffix",
            "evaluate_expressions",
            "include_model",
            "include_network",
            "overwrite",
            "pretty_formatting",
            "TextReaction",
            "TextSpecies",
        ]
        self.arg_dict["writeNetwork"] = [
            "format",
            "prefix",
            "suffix",
            "evaluate_expressions",
            "include_model",
            "include_network",
            "overwrite",
            "pretty_formatting",
            "TextReaction",
            "TextSpecies",
        ]
        self.arg_dict["writeXML"] = [
            "format",
            "prefix",
            "suffix",
            "evaluate_expressions",
            "include_model",
            "include_network",
            "overwrite",
            "pretty_formatting",
            "TextReaction",
            "TextSpecies",
        ]
        self.arg_dict["writeSBML"] = ["prefix", "suffix"]
        self.arg_dict["writeMfile"] = [
            "prefix",
            "suffix",
            "t_start",
            "t_end",
            "n_steps",
            "atol",
            "rtol",
            "max_step",
            "bdf",
            "maxOrder",
            "stats",
        ]
        self.arg_dict["writeMexfile"] = [
            "prefix",
            "suffix",
            "t_start",
            "t_end",
            "n_steps",
            "atol",
            "rtol",
            "max_step",
            "max_num_steps",
            "max_err_test_fails",
            "max_conv_fails",
            "stiff",
            "sparse",
        ]
        self.arg_dict["writeMDL"] = ["prefix", "suffix"]
        self.arg_dict["visualize"] = [
            "type",
            "help",
            "suffix",
            "each",
            "background",
            "groups",
            "collapse",
            "filter",
            "level",
            "textonly",
            "opts",
        ]
        # no_setter_syntax
        self.arg_dict["setConcentration"] = []
        self.arg_dict["addConcentration"] = []
        self.arg_dict["setParameter"] = []
        self.arg_dict["saveParameters"] = []
        self.arg_dict["quit"] = None
        self.arg_dict["setModelName"] = []
        self.arg_dict["substanceUnits"] = []
        self.arg_dict["version"] = []
        self.arg_dict["setOption"] = []
        # square_braces
        self.arg_dict["saveConcentrations"] = []
        self.arg_dict["resetConcentrations"] = []
        self.arg_dict["resetParameters"] = []

    def is_before_model(self, action_name):
        if action_name in self.before_model:
            return True
        return False


def find_BNG_path(BNGPATH=None):
    """
    A simple function finds the path to BNG2.pl from
    * Environment variable
    * Assuming it's under PATH
    * Given optional path as argument

    Usage: test_bngexec(path)
           test_bngexec()

    Arguments
    ---------
    BNGPATH : str
        (optional) path to the folder that contains BNG2.pl
    """
    # TODO: Figure out how to use the BNG2.pl if it's set
    # in the PATH variable. Solution: set os.environ BNGPATH
    # and make everything use that route

    # Let's keep up the idea we pull this path from the environment
    if BNGPATH is None:
        try:
            BNGPATH = os.environ["BNGPATH"]
        except:
            pass
    # if still none, try pulling it from cmd line
    if BNGPATH is None:
        bngexec = "BNG2.pl"
        if test_bngexec(bngexec):
            # print("BNG2.pl seems to be working")
            # get the source of BNG2.pl
            BNGPATH = spawn.find_executable("BNG2.pl")
            BNGPATH, _ = os.path.split(BNGPATH)
    else:
        bngexec = os.path.join(BNGPATH, "BNG2.pl")
        if not test_bngexec(bngexec):
            RuntimeError("BNG2.pl is not working")
    return BNGPATH, bngexec


def test_bngexec(bngexec):
    """
    A simple function that test if BNG2.pl given runs

    Usage: test_bngexec(path)

    Arguments
    ---------
    bngexec : str
        path to BNG2.pl to test
    """
    command = ["perl", bngexec]
    rc, _ = run_command(command, suppress=True)
    if rc == 0:
        return True
    else:
        return False


def run_command(command, suppress=False):
    if suppress:
        process = subprocess.Popen(
            command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, bufsize=-1
        )
        return process.poll(), None
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, encoding="utf8")
        out = []
        while True:
            output = process.stdout.readline()
            if output == "" and process.poll() is not None:
                break
            if output:
                o = output.strip()
                out.append(o)
                print(o)
        rc = process.poll()
        return rc, out
