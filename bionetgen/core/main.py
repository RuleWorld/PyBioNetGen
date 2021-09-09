from bionetgen.tools import BNGPlotter
from bionetgen.tools import BNGInfo
from bionetgen.tools import BNGVisualize
from bionetgen.tools import BNGCLI

import os, sys


# TODO Consolidate how config is being accessed. It's
# almost like each function accesses the configs from
# a different path


def runCLI(config, args):
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


def plotDAT(inp, out=".", kw=dict()):
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
    # if we want to plot directly into the folder
    # we are in we need to get the path correctly
    if out == ".":
        path, fname = os.path.split(inp)
        fnoext, ext = os.path.splitext(fname)
        out = os.path.join(path, "{}.png".format(fnoext))
    # use the plotter object to get the plot
    plotter = BNGPlotter(inp, out, **kw)
    plotter.plot()


def printInfo(config, args):
    """
    Uses BNGInfo class to print BioNetGen information using
    arguments and config from Cement framework.
    """
    # this pulls out the arguments
    # inp_file = args.input
    # output = args.output
    # if you set args.bngpath it should take precedence
    # config_bngpath = config.get("bionetgen", "bngpath")
    # and instantiates the CLI object
    info = BNGInfo(config=config)
    info.gatherInfo()
    info.messageGeneration()
    info.run()


def visualizeModel(config, args):
    """
    Uses BNGVisualize class to visualize BNGL models using
    arguments and configuration from Cement framework.
    """
    inp = args.input
    out = args.output
    vtype = args.type
    # if you set args.bngpath it should take precedence
    config_bngpath = config.get("bionetgen", "bngpath")
    viz = BNGVisualize(inp, output=out, vtype=vtype, bngpath=config_bngpath)
    viz.run()
