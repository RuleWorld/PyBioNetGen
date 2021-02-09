import cement, os, platform, subprocess
import bionetgen as bng
from cement.core.exc import CaughtSignal
from .core.exc import BioNetGenError
from .core.main import runCLI
from .core.main import plotDAT 
from .core.notebook import BNGNotebook

# pull defaults 
CONFIG = bng.defaults.config
VERSION_BANNER = bng.defaults.banner

class BNGBase(cement.Controller):
    ''' Base controller for BioNetGen CLI '''

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
                (['-v','--version'],dict(action="version",
                                         version=VERSION_BANNER)),
                # (['-s','--sedml'],dict(type=str,
                #                        default=CONFIG['bionetgen']['bngpath'],
                #                        help="Optional path to SED-ML file, if available the simulation \
                #                              protocol described in SED-ML will be ran")),
        ]

    # This overwrites the default behavior 
    # and runs the CLI object from core 
    # which in turn just calls BNG2.pl 
    @cement.ex(
            help="Runs a given model using BNG2.pl",
            arguments=[
                (["-i","--input"],{"help":"Path to BNGL file (required)",
                                   "default": None,
                                   "type": str,
                                   "required": True}),
                (["-o","--output"],{"help":"Optional path to output folder (default: \".\")",
                                    "default": ".",
                                    "type": str})
            ]
    )
    def run(self):
        args = self.app.pargs
        runCLI(self.app.config, args)

    @cement.ex(
            help="Starts a Jupyter notebook to help run and analyze \
                  bionetgen models",
            arguments=[
                (["-i","--input"],{"help":"Path to BNGL file to use with notebook",
                                   "default": None,
                                   "type": str,
                                   "required": False}),
            ]
    )
    def notebook(self):
        """ Notebook subcommand that boots up a Jupyter notebook """
        args = self.app.pargs
        if args.input is not None:
            # we want to use the template to write a custom notebok
            notebook = BNGNotebook(CONFIG["bionetgen"]["notebook"]["template"], INPUT_ARG=args.input)
        else:
            # just use the basic notebook
            notebook = BNGNotebook(CONFIG["bionetgen"]["notebook"]["path"])
        # write the notebook out
        notebook.write(CONFIG["bionetgen"]["notebook"]["name"])
        # open the notebook with nbopen
        rc = subprocess.run(["nbopen", CONFIG["bionetgen"]["notebook"]["name"]], stdout=bng.defaults.stdout)

    @cement.ex(
            help="Rudimentary plotting of gdat/cdat/scan files",
            arguments=[
                (["-i","--input"],{"help":"Path to .gdat/.cdat file to use plot",
                                   "default": None,
                                   "type": str,
                                   "required": True}),
                (["-o","--output"],{"help":"Optional path for the plot (default: \"$model_name.png\")",
                                    "default": ".",
                                    "type": str}),
                (["--legend"],{"help":"To plot the legend or not (default: False)",
                                   "default": False,
                                   "action": "store_true",
                                   "required": False}),
                (["--xmin"],{"help":"x-axis minimum (default: determined from data)",
                                   "default": None}),
                (["--xmax"],{"help":"x-axis maximum (default: determined from data)",
                                   "default": False}),
                (["--ymin"],{"help":"y-axis minimum (default: determined from data)",
                                   "default": False}),
                (["--ymax"],{"help":"y-axis maximum (default: determined from data)",
                                   "default": False}),
                (["--xlabel"],{"help":"x-axis label (default: time)",
                                   "default": False}),
                (["--ylabel"],{"help": "y-axis label (default: concentration)",
                                   "default": False}),
                (["--title"],{"help": "title of plot (default: determined from input file)",
                                   "default": False})
            ]
    )
    def plot(self):
        """ Notebook subcommand that boots up a Jupyter notebook """
        args = self.app.pargs
        # we need to have gdat/cdat files
        assert args.input.endswith(".gdat") or args.input.endswith(".cdat") or args.input.endswith(".scan"), "Input file has to be either a gdat or a cdat file"
        plotDAT(args.input, args.output, kw=dict(args._get_kwargs()))

class BioNetGen(cement.App):
    """BioNetGen CLI primary application."""

    class Meta:
        label = 'bionetgen'

        # configuration defaults
        config_defaults = CONFIG

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = [
            'yaml',
            'colorlog',
        ]

        # configuration handler
        config_handler = 'configparser'

        # configuration file suffix
        config_file_suffix = '.conf'

        # add current folder to the list of config dirs
        config_files = [
            './.{}.conf'.format(label)
        ]

        # set the log handler
        log_handler = 'colorlog'

        # register handlers
        handlers = [
            BNGBase
        ]

class BioNetGenTest(cement.TestApp,BioNetGen):
    """ A sub-class of BioNetGen for testing """

    class Meta:
        label = "bionetgen"


def main():
    with BioNetGen() as app:
        try:
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except BioNetGenError as e:
            print('BioNetGenError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
