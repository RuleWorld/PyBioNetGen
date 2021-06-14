from bionetgen.modelapi.utils import run_command
import cement, os, platform, subprocess
import bionetgen as bng
from cement.core.exc import CaughtSignal
from .core.exc import BioNetGenError
from .core.main import runCLI
from .core.main import plotDAT
from .core.notebook import BNGNotebook

# pull defaults defined in core/defaults
CONFIG = bng.defaults.config
VERSION_BANNER = bng.defaults.banner


class BNGBase(cement.Controller):
    """
    Base cement controller for BioNetGen CLI

    Used to set meta attributes like program name (label) as well
    as command line arguments. Each method is a subcommand in the
    command line with it's own command line arguments.

    Subcommands
    -------
    run
        runs a model given by -i in folder given by -o
    notebook
        generates and opens a notebook for a model given by -i, optional
    plot
        plots a gdat/cdat/scan file given by -i into file supplied by -o
    """

    class Meta:
        label = "bionetgen"
        description = "A simple CLI to bionetgen <https://bionetgen.org>. Note that you need Perl installed."
        help = "bionetgen"
        arguments = [
            # TODO figure out a good solution for when bngpath is set from config file AND CLI
            # until then we'll disable the CLI argument
            # (['-bp','--bngpath'],dict(type=str,
            #                           default=CONFIG['bionetgen']['bngpath'],
            #                           help="Optional path to BioNetGen folder you want the CLI to use")),
            # TODO: Auto-load in BioNetGen version here
            (["-v", "--version"], dict(action="version", version=VERSION_BANNER)),
            # (['-s','--sedml'],dict(type=str,
            #                        default=CONFIG['bionetgen']['bngpath'],
            #                        help="Optional path to SED-ML file, if available the simulation \
            #                              protocol described in SED-ML will be ran")),
        ]

    # This overwrites the default behavior and runs the CLI object from core/main
    # which in turn just calls BNG2.pl with the supplied options
    @cement.ex(
        help="Runs a given model using BNG2.pl",
        arguments=[
            (
                ["-i", "--input"],
                {
                    "help": "Path to BNGL file (required)",
                    "default": None,
                    "type": str,
                    "required": True,
                },
            ),
            (
                ["-o", "--output"],
                {
                    "help": 'Optional path to output folder (default: ".")',
                    "default": ".",
                    "type": str,
                },
            ),
        ],
    )
    def run(self):
        """
        This is the main run functionality of the CLI.

        It uses a convenience function defined in core/main
        to run BNG2.pl using subprocess, given the set of arguments
        in the command line and the configuraions set by the defaults
        as well as the end-user.
        """
        args = self.app.pargs
        runCLI(self.app.config, args)

    @cement.ex(
        help="Starts a Jupyter notebook to help run and analyze \
                  bionetgen models",
        arguments=[
            (
                ["-i", "--input"],
                {
                    "help": "Path to BNGL file to use with notebook",
                    "default": None,
                    "type": str,
                    "required": False,
                },
            ),
            (
                ["-o", "--output"],
                {
                    "help": "(optional) File to write the notebook in",
                    "default": "",
                    "type": str,
                },
            ),
            (
                ["-op", "--open"],
                {
                    "help": "(optional) If given, the notebook will by opened using nbopen",
                    "action": "store_true",
                },
            ),
        ],
    )
    def notebook(self):
        """
        Notebook subcommand that boots up a Jupyter notebook using the
        nbopen library. It uses a BNGNotebook class defined in core/notebook.

        The default template can be found under assets and in the future
        will likely be replaced by a standard templating tool (e.g. Jinja).

        The default base template is agnostic to the model and if -i is given
        the template then will be adjusted to load in the model supplied.
        """
        args = self.app.pargs
        if args.input is not None:
            # we want to use the template to write a custom notebok
            notebook = BNGNotebook(
                CONFIG["bionetgen"]["notebook"]["template"], INPUT_ARG=args.input
            )
        else:
            # just use the basic notebook
            notebook = BNGNotebook(CONFIG["bionetgen"]["notebook"]["path"])
        # find our file name
        if len(args.output) == 0:
            fname = CONFIG["bionetgen"]["notebook"]["name"]
        else:
            fname = args.output
        # write the notebook out
        notebook.write(fname)
        # open the notebook with nbopen
        stdout = getattr(subprocess, CONFIG["bionetgen"]["stdout"])
        stderr = getattr(subprocess, CONFIG["bionetgen"]["stderr"])
        if args.open:
            # rc = subprocess.run(["nbopen", fname], stdout=stdout, stderr=stderr)
            # rc = subprocess.run(["nbopen", fname], capture_output=True, bufsize=1)
            command = ["nbopen", fname]
            rc = run_command(command)

    @cement.ex(
        help="Rudimentary plotting of gdat/cdat/scan files",
        arguments=[
            (
                ["-i", "--input"],
                {
                    "help": "Path to .gdat/.cdat file to use plot",
                    "default": None,
                    "type": str,
                    "required": True,
                },
            ),
            (
                ["-o", "--output"],
                {
                    "help": 'Optional path for the plot (default: "$model_name.png")',
                    "default": ".",
                    "type": str,
                },
            ),
            (
                ["--legend"],
                {
                    "help": "To plot the legend or not (default: False)",
                    "default": False,
                    "action": "store_true",
                    "required": False,
                },
            ),
            (
                ["--xmin"],
                {
                    "help": "x-axis minimum (default: determined from data)",
                    "default": None,
                },
            ),
            (
                ["--xmax"],
                {
                    "help": "x-axis maximum (default: determined from data)",
                    "default": False,
                },
            ),
            (
                ["--ymin"],
                {
                    "help": "y-axis minimum (default: determined from data)",
                    "default": False,
                },
            ),
            (
                ["--ymax"],
                {
                    "help": "y-axis maximum (default: determined from data)",
                    "default": False,
                },
            ),
            (["--xlabel"], {"help": "x-axis label (default: time)", "default": False}),
            (
                ["--ylabel"],
                {"help": "y-axis label (default: concentration)", "default": False},
            ),
            (
                ["--title"],
                {
                    "help": "title of plot (default: determined from input file)",
                    "default": False,
                },
            ),
        ],
    )
    def plot(self):
        """
        Plotting subcommand for very basic plotting using a convenience function
        defined in core/main.

        Currently we support gdat/cdat/scan file plotting, in a very basic manner.
        This command expects a space separated file where each column is a series.
        The first column is used for the x-axis and the rest is used as y-axis
        and every series is plotted.

        See bionetgen plot -h for all the allowed options.
        """
        args = self.app.pargs
        # we need to have gdat/cdat files
        assert (
            args.input.endswith(".gdat")
            or args.input.endswith(".cdat")
            or args.input.endswith(".scan")
        ), "Input file has to be either a gdat or a cdat file"
        plotDAT(args.input, args.output, kw=dict(args._get_kwargs()))


class BioNetGen(cement.App):
    """
    Cement app for BioNetGen CLI

    Used to set configuration options like config default,
    exiting on close and setting log handler. Currently set
    attributes are below.

    Attributes
    ----------
    label : str
        name of the application
    config_defaults : str
        the default set of configuration options, set in BNGDefaults object
    config_handler: str
        the name of the config handler, determines the syntax of the config files
    config_file_suffix: str
        the suffix to be used for config files
    config_files: list of str
        additional list of config files to enable
    exit_on_close : boolean
        determine if the app should exit when the key function is ran
    extensions : list of str
        extensions to be used with cement framework
    log_handler: str
        name of the log handler
    handlers: list of obj
        list of objects derived from cement.Controller that handles the actual CLI
    """

    class Meta:
        label = "bionetgen"

        # configuration defaults
        config_defaults = CONFIG

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            "yaml",
            "colorlog",
        ]

        # configuration handler
        config_handler = "configparser"

        # configuration file suffix
        config_file_suffix = ".conf"

        # add current folder to the list of config dirs
        config_files = ["./.{}.conf".format(label)]

        # set the log handler
        log_handler = "colorlog"

        # register handlers
        handlers = [BNGBase]


class BioNetGenTest(cement.TestApp, BioNetGen):
    """
    A sub-class of BioNetGen CLI application for testing
    purposes. See tests/test_bionetgen.py for examples.
    """

    class Meta:
        label = "bionetgen"


def main():
    with BioNetGen() as app:
        try:
            app.run()

        except AssertionError as e:
            print("AssertionError > %s" % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback

                traceback.print_exc()

        except BioNetGenError as e:
            print("BioNetGenError > %s" % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback

                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print("\n%s" % e)
            app.exit_code = 0


if __name__ == "__main__":
    main()
