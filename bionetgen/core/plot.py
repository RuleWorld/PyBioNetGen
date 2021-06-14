import os
import numpy as np
import seaborn as sbrn
import matplotlib.pyplot as plt
from bionetgen.core import BNGResult


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

    def __init__(self, inp, out, **kwargs):
        # read input and output paths
        self.inp = inp
        self.out = out
        # load in the result
        self.result = BNGResult(direct_path=inp)
        # get the keyword arguments
        self.kwargs = kwargs

    def plot(self):
        # let's determine the type of plot we are doing
        if (
            self.result.file_extension == ".gdat"
            or self.result.file_extension == ".cdat"
        ):
            self._datplot()
        elif self.result.file_extension == ".scan":
            self._datplot()
        else:
            print(
                "File type not recognized, only gdat/cdat and scan files are implemented"
            )
            raise NotImplementedError

    def _datplot(self):
        # get the data out of result object
        self.data = self.result.results[self.result.file_name]
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

        fax.set_xlim(xmin, xmax)
        fax.set_ylim(ymin, ymax)
        # labels and title
        _ = plt.xlabel(self.kwargs.get("xlabel") or x_name)
        _ = plt.ylabel(self.kwargs.get("ylabel") or "concentration")
        _ = plt.title(self.kwargs.get("title") or self.result.file_name)

        # save the figure
        plt.savefig(self.out)
