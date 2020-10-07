import cement, os
from cement import init_defaults
from cement.core.exc import CaughtSignal
from .core.exc import BioNetGenError
from .core.main import runCLI

# configuration defaults
# TODO: we want to install the appropriate BNG distro on setup 
# and not include it w/ the package. For now, this will do 
# for testing purposes
CONFIG = init_defaults('bionetgen')
CONFIG['bionetgen']['bngpath'] = os.path.join(os.path.dirname(__file__), "bng")

class BNGBase(cement.Controller):
    ''' Base controller for BioNetGen CLI '''

    class Meta:
        label = "base"
        description = "A simple CLI to bionetgen <https://bionetgen.org>. Note that you need Perl installed."
        help = "bionetgen"
        arguments = [
                (['-i', '--input'],dict(type=str,
                                        required=True,
                                        help="Path to BNGL or SBML file")), 
                (['-o','--output'],dict(type=str, 
                                        default=".",
                                        help="Directory to save the results into, default is '.'")),
                (['-s','--sedml'],dict(type=str,
                                       default=CONFIG['bionetgen']['bngpath'],
                                       help="Optional path to SED-ML file, if available the simulation \
                                             protocol described in SED-ML will be ran")),
                (['-bp','--bngpath'],dict(type=str,
                                          default=None,
                                          help="Optional path to BioNetGen folder you want the CLI to use")),
                # TODO: Auto-load in BioNetGen version here
                (['-v','--version'],dict(action="version",
                                         version="0.0.1")),
        ]

    @cement.ex(hide=True)
    def _default(self):
        args = self.app.pargs
        runCLI(args)

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
