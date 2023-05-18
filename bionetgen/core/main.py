import subprocess, os, sys
from bionetgen.core.tools import BNGInfo
from bionetgen.core.tools import BNGVisualize
from bionetgen.core.tools import BNGCLI
from bionetgen.core.tools import BNGGdiff
from bionetgen.core.tools import BNGJSVisualize
from bionetgen.core.notebook import BNGNotebook
from bionetgen.core.utils.utils import run_command


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
    app.log.debug("Pulling BNG path from config", f"{__file__} : runCLI()")
    config_bngpath = config.get("bionetgen", "bngpath")
    # and instantiates the CLI object
    app.log.debug("Instantiating BNGCLI object", f"{__file__} : runCLI()")
    cli = BNGCLI(inp_file, output, config_bngpath, log_file=log_file, app=app)
    cli.stdout = config.get("bionetgen", "stdout")
    cli.stderr = config.get("bionetgen", "stderr")
    app.log.debug("Running", f"{__file__} : runCLI()")
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
    # we need to have gdat/cdat files
    # TODO: Transition to BNGErrors and logging
    assert (
        args.input.endswith(".gdat")
        or args.input.endswith(".cdat")
        or args.input.endswith(".scan")
    ), "Input file has to be either a gdat or a cdat file"
    inp = args.input
    out = args.output
    kw = dict(args._get_kwargs())
    # if we want to plot directly into the folder
    # we are in we need to get the path correctly
    if out == ".":
        path, fname = os.path.split(inp)
        fnoext, ext = os.path.splitext(fname)
        out = os.path.join(path, "{}.png".format(fnoext))
    # use the plotter object to get the plot
    from bionetgen.core.tools import BNGPlotter

    app.log.debug("Instantiating BNGPlotter object", f"{__file__} : plotDAT()")
    plotter = BNGPlotter(inp, out, app=app, **kw)
    app.log.debug("Plotting", f"{__file__} : plotDAT()")
    plotter.plot()


def runAtomizeTool(app):
    """
    Uses AtomizeTool class to run atomizer from a set of arguments
    """
    # pull args/config
    args = app.pargs
    config = app.config
    # run AtomizeTool
    from bionetgen.atomizer import AtomizeTool

    app.log.debug("Instantiating AtomizeTool object", f"{__file__} : runAtomizeTool()")
    a = AtomizeTool(parser_namespace=args, app=app)
    # do config specific stuff here if need be, or remove the config requirement
    app.log.debug("Atomizing", f"{__file__} : runAtomizeTool()")
    resArr = a.run()
    if args.write_scts:
        import json

        model_name = os.path.splitext(args.input)[0]
        with open(f"{model_name}_scts.json", "w") as f:
            json.dump(resArr.database.scts, f, ensure_ascii=False, indent=4)
        if args.write_sct_graphs:
            import pyyed

            for graph_name in resArr.database.scts:
                G = pyyed.Graph()
                graph_dict = resArr.database.scts[graph_name]
                for node_name in graph_dict:
                    if node_name not in G.nodes:
                        G.add_node(
                            node_name, shape="roundrectangle", shape_fill="#c6c6c6"
                        )
                    for node_arr in graph_dict[node_name]:
                        # this is still a list
                        for conn_name in node_arr:
                            if conn_name not in G.nodes:
                                G.add_node(
                                    conn_name,
                                    shape="roundrectangle",
                                    shape_fill="#c6c6c6",
                                )
                            G.add_edge(node_name, conn_name)
                G.write_graph(f"{model_name}_{graph_name}.graphml", pretty_print=True)


def printInfo(app):
    """
    Uses BNGInfo class to print BioNetGen information using
    arguments and config from Cement framework.
    """
    config = app.config
    app.log.debug("Instantiating BNGInfo object", f"{__file__} : printInfo()")
    info = BNGInfo(config=config, app=app)
    app.log.debug("Gathering and printing info", f"{__file__} : printInfo()")
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
    app.log.debug("Pulling BNG path from config", f"{__file__} : visualizeModel()")
    # if you set args.bngpath it should take precedence
    config_bngpath = config.get("bionetgen", "bngpath")
    # run visualize tool
    app.log.debug("Instantiating BNGVisualize object", f"{__file__} : visualizeModel()")
    viz = BNGVisualize(inp, output=out, vtype=vtype, bngpath=config_bngpath, app=app)
    app.log.debug("Visualizing", f"{__file__} : visualizeModel()")
    viz.run()


def graphDiff(app):
    """
    Uses BNGGdiff object to calculate differences between two graphs
    (only works with graphml files generated by BioNetGen)
    """
    # pull args and config for the tool
    args = app.pargs
    # if you set args.bngpath it should take precedence
    app.log.debug("Instantiating BNGGdiff object", f"{__file__} : graphDiff()")
    gdiff = BNGGdiff(
        args.input,
        args.input2,
        out=args.output,
        out2=args.output2,
        mode=args.mode,
        colors=args.colors,
        app=app,
    )
    app.log.debug("Calculating graph diff", f"{__file__} : graphDiff()")
    gdiff.run()


def generate_notebook(app):
    """
    Uses BNGNotebook class to write a Jupyter notebook from a
    given set of command line arguments
    """
    args = app.pargs
    if args.input is not None:
        # we want to use the template to write a custom notebok
        # TODO: Transition to BNGErrors and logging
        assert args.input.endswith(
            ".bngl"
        ), f"File {args.input} doesn't have bngl extension!"
        try:
            app.log.debug("Loading model", f"{__file__} : notebook()")
            import bionetgen

            m = bionetgen.bngmodel(args.input)
            str(m)
        except:
            app.log.error("Failed to load model", f"{__file__} : notebook()")
            raise RuntimeError(f"Couldn't import given model: {args.input}!")
        notebook = BNGNotebook(
            app.config["bionetgen"]["notebook"]["template"],
            INPUT_ARG=args.input,
        )
    else:
        # just use the basic notebook
        notebook = BNGNotebook(app.config["bionetgen"]["notebook"]["path"])
    # find our file name
    if len(args.output) == 0:
        fname = app.config["bionetgen"]["notebook"]["name"]
    else:
        fname = args.output
    # write the notebook out
    if os.path.isdir(fname):
        if args.input is not None:
            basename = os.path.basename(args.input)
            mname = basename.replace(".bngl", "")
            fname = mname + ".ipynb"
        else:
            mname = app.config["bionetgen"]["notebook"]["name"]
            fname = os.path.join(args.output, mname)

    app.log.debug(f"Writing notebook to file: {fname}", f"{__file__} : notebook()")
    notebook.write(fname)
    # open the notebook with nbopen
    # TODO: deal with stdout/err
    app.log.debug(
        f"Attempting to open notebook {fname} with nbopen",
        f"{__file__} : notebook()",
    )
    stdout = getattr(subprocess, app.config["bionetgen"]["stdout"])
    stderr = getattr(subprocess, app.config["bionetgen"]["stderr"])
    if args.open:
        command = ["nbopen", fname]
        rc, _ = run_command(command)

def writeJSvis(app):
    """
    Uses BNGJSVisualize class to write default JavaScript visualization settings
    from the BNGL models using arguments and configuration.
    """
    # pull args/config from app
    args = app.pargs
    config = app.config
    # pull relevant arguments for the tool
    inp = args.input
    out = args.output
    app.log.debug("Pulling BNG path from config", f"{__file__} : writeJSvis()")
    # if you set args.bngpath it should take precedence
    config_bngpath = config.get("bionetgen", "bngpath")
    # run visualize tool
    app.log.debug("Instantiating BNGJSVisualize object", f"{__file__} : writeJSvis()")
    jsviz = BNGJSVisualize(inp, output=out, bngpath=config_bngpath, app=app)
    app.log.debug("Visualizing", f"{__file__} : writeJSvis()")
    jsviz.run()
