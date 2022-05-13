import os
from bionetgen.tools import BNGInfo
from bionetgen.tools import BNGVisualize
from bionetgen.tools import BNGCLI
from bionetgen.tools import BNGGdiff

import os, sys


# TODO Consolidate how config is being accessed. It's
# almost like each function accesses the configs from
# a different path
def runCLI(app):
    """
    Convenience function to run BNG2.pl from the CLI app

    Usage: runCLI(config, args)

    Arguments
    ---------
    config : dict
        configuration dictionary from BioNetGen cement app
    args :  argparse.Namespace
        arguments parsed from the command line with argparser.
    """
    args = app.pargs
    config = app.config
    # this pulls out the arguments
    sys.tracebacklimit = args.traceback_depth
    inp_file = args.input
    output = args.output
    log_file = args.log_file
    # if you set args.bngpath it should take precedence
    config_bngpath = config.get("bionetgen", "bngpath")
    # and instantiates the CLI object
    cli = BNGCLI(inp_file, output, config_bngpath, log_file=log_file)
    cli.stdout = config.get("bionetgen", "stdout")
    cli.stderr = config.get("bionetgen", "stderr")
    cli.run()


def plotDAT(app):
    """
    Convenience function to plot dat/scan files from the CLI

    Usage: plotDAT(inp, out, kw)

    Arguments
    ---------
    inp : str
        input gdat/cdat/scan file to plot
    out : str
        (optional) output file path, can be used to define the
        output format as well. Default is the current folder,
        filename is the same as the input file and default format
        is PNG.
    kw : dict
        (optional) this is a set of keyword arguments you want to
        pass for certain matplotlib options. Check -h for details
    """
    args = app.pargs
    inp = args.input
    out = args.output
    kw=dict(args._get_kwargs())
    # if we want to plot directly into the folder
    # we are in we need to get the path correctly
    if out == ".":
        path, fname = os.path.split(inp)
        fnoext, ext = os.path.splitext(fname)
        out = os.path.join(path, "{}.png".format(fnoext))
    # use the plotter object to get the plot
    from bionetgen.tools import BNGPlotter

    plotter = BNGPlotter(inp, out, **kw)
    plotter.plot()


def runAtomizeTool(app):
    # pull args/config
    args = app.args
    config = app.config
    # run AtomizeTool
    from bionetgen.atomizer import AtomizeTool

    a = AtomizeTool(parser_namespace=args)
    # do config specific stuff here if need be, or remove the config requirement
    a.run()


def printInfo(app):
    """
    Uses BNGInfo class to print BioNetGen information using
    arguments and config from Cement framework.
    """
    config = app.config
    info = BNGInfo(config=config)
    info.gatherInfo()
    info.messageGeneration()
    info.run()


def visualizeModel(app):
    """
    Uses BNGVisualize class to visualize BNGL models using
    arguments and configuration from Cement framework.
    """
    # pull args/config from app
    args = app.pargs
    config = app.config
    # pull relevant arguments for the tool
    inp = args.input
    out = args.output
    vtype = args.type
    # if you set args.bngpath it should take precedence
    viz = BNGVisualize(inp, output=out, vtype=vtype)
    viz.run()


def graphDiff(app):
    # pull args and config for the tool
    args = app.pargs
    # if you set args.bngpath it should take precedence
    gdiff = BNGGdiff(
        args.input,
        args.input2,
        out=args.output,
        out2=args.output2,
        mode=args.mode,
        colors=args.colors,
    )
    gdiff.run()
