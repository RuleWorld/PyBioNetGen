import cement, os, platform, subprocess
import bionetgen as bng
from cement.core.exc import CaughtSignal
from .core.exc import BioNetGenError
from .core.main import runCLI
from .core.notebook import BNGNotebook

# pull defaults 
CONFIG = bng.defaults.config
VERSION_BANNER = bng.defaults.banner

class BNGBase(cement.Controller):
    ''' Base controller for BioNetGen CLI '''

    class Meta:
        label = "base"
        description = "A simple CLI to bionetgen <https://bionetgen.org>. Note that you need Perl installed."
        help = "bionetgen"
        arguments = [
                (['-i', '--input'],dict(type=str,
                                        default=None,
                                        help="Path to BNGL or SBML file")), 
                (['-o','--output'],dict(type=str, 
                                        default=".",
                                        help="Directory to save the results into, default is '.'")),
                # (['-s','--sedml'],dict(type=str,
                #                        default=CONFIG['bionetgen']['bngpath'],
                #                        help="Optional path to SED-ML file, if available the simulation \
                #                              protocol described in SED-ML will be ran")),
                (['-bp','--bngpath'],dict(type=str,
                                          default=CONFIG['bionetgen']['bngpath'],
                                          help="Optional path to BioNetGen folder you want the CLI to use")),
                # TODO: Auto-load in BioNetGen version here
                (['-v','--version'],dict(action="version",
                                         version=VERSION_BANNER)),
        ]

    # This overwrites the default behavior 
    # and runs the CLI object from core 
    # which in turn just calls BNG2.pl 
    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        if args.input is None:
            # TODO: improve this behavior by showing help after automatically
            print("Please give an input BNGL file with the -i option, see -h or --help to see help, quitting")
        else:
            runCLI(args)

    @cement.ex(
            help="Starts a Jupyter notebook to help run and analyze \
                  bionetgen models",
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
        config_handler = 'yaml'

        # configuration file suffix
        config_file_suffix = '.yml'

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
