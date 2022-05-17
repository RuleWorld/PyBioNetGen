import os
import numpy as np
from bionetgen.tools import BNGResult


class BNGPlotter:
    """
    Class that does basic plotting for gdat/cdat files

    Usage BNGPlotter(inp, out, kwargs)

    Arguments
    ---------
    inp : str
        input file path, gdat/cdat/scan file
    out : str
        output file path
    kwargs : dict
        keywords arguments for matplotlib. For details check
        bionetgen plot -h

    Methods
    -------
    plot()
        plots the data from the input file and saves it to
        output file the class is initialized with
    """

    def __init__(self, inp, out, app=None, **kwargs):
        self.app = app
        if self.app is not None:
            self.app.log.debug(
                "Setting up BNGPlotter object", f"{__file__} : BNGPlotter.__init__()"
            )
        # read input and output paths
        self.inp = inp
        self.out = out
        # load in the result
        if self.app is not None:
            self.app.log.debug(
                f"Loading BNG result file {inp}", f"{__file__} : BNGPlotter.__init__()"
            )
        self.result = BNGResult(direct_path=inp, app=self.app)
        # get the keyword arguments
        self.kwargs = kwargs

    def plot(self):
        # let's determine the type of plot we are doing
        if (
            self.result.file_extension == ".gdat"
            or self.result.file_extension == ".cdat"
        ):
            if self.app is not None:
                self.app.log.debug(
                    "Input is a .gdat/.cdat file", f"{__file__} : BNGPlotter.plot()"
                )
            self._datplot()
        elif self.result.file_extension == ".scan":
            if self.app is not None:
                self.app.log.debug(
                    "Input is a .scan file", f"{__file__} : BNGPlotter.plot()"
                )
            self._datplot()
        else:
            if self.app is not None:
                self.app.log.error(
                    "File type not recognized, only gdat/cdat and scan files are implemented", f"{__file__} : BNGPlotter.plot()"
                )
            print(
                "File type not recognized, only gdat/cdat and scan files are implemented"
            )
            raise NotImplementedError

    def _datplot(self):
        if self.app is not None:
            self.app.log.debug(
                f"Plotting .gdat/.cdat/.scan file {self.result.file_name}", f"{__file__} : BNGPlotter._datplot()"
            )
        import seaborn as sbrn
        import matplotlib.pyplot as plt

        # get the data out of result object
        self.data = self.result[self.result.file_name]
        # get species names
        names = self.data.dtype.names
        x_name = names[0]
        # loop over and plot them all
        ctr = 0
        ax = None
        for name in names:
            if name == x_name:
                continue
            ax = sbrn.lineplot(x=self.data[x_name], y=self.data[name], label=name)
            ctr += 1
        # TODO: Transition to BNGErrors and logging
        assert ax is not None, "No data columns are found in file {}".format(
            self.result.direct_path
        )

        fax = ax.get_figure().gca()
        if not self.kwargs.get("legend", False):
            fax.legend().remove()
        oxmin, oxmax = fax.get_xlim()
        oymin, oymax = fax.get_ylim()

        xmin = self.kwargs.get("xmin", False) or oxmin
        xmax = self.kwargs.get("xmax", False) or oxmax
        ymin = self.kwargs.get("ymin", False) or oymin
        ymax = self.kwargs.get("ymax", False) or oymax
        # TODO: Transition to BNGErrors and logging
        assert xmax > xmin, "--xmin is bigger than --xmax!"
        assert ymax > ymin, "--ymin is bigger than --ymax!"

        fax.set_xlim(left=xmin, right=xmax)
        fax.set_ylim(bottom=ymin, top=ymax)
        # labels and title
        _ = plt.xlabel(self.kwargs.get("xlabel") or x_name)
        _ = plt.ylabel(self.kwargs.get("ylabel") or "concentration")
        _ = plt.title(self.kwargs.get("title") or self.result.file_name)

        if self.app is not None:
            self.app.log.debug(
                f"Saving figure to {self.out}", f"{__file__} : BNGPlotter._datplot()"
            )
        # save the figure
        plt.savefig(self.out)
