import os
import numpy as np
from bionetgen.core.tools import BNGResult
from bionetgen.core.utils.logging import BNGLogger


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
        self.logger = BNGLogger(app=self.app)
        self.logger.debug(
            "Setting up BNGPlotter object", loc=f"{__file__} : BNGPlotter.__init__()"
        )
        # read input and output paths
        self.inp = inp
        self.out = out
        # load in the result
        self.logger.debug(
            f"Loading BNG result file {inp}", loc=f"{__file__} : BNGPlotter.__init__()"
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
            self.logger.debug(
                "Input is a .gdat/.cdat file", loc=f"{__file__} : BNGPlotter.plot()"
            )
            self._datplot()
        elif self.result.file_extension == ".scan":
            self.logger.debug(
                "Input is a .scan file", loc=f"{__file__} : BNGPlotter.plot()"
            )
            self._datplot()
        else:
            self.logger.error(
                "File type not recognized, only gdat/cdat and scan files are implemented",
                loc=f"{__file__} : BNGPlotter.plot()",
            )
            raise NotImplementedError

    def _datplot(self):
        self.logger.debug(
            f"Plotting .gdat/.cdat/.scan file {self.result.file_name}",
            loc=f"{__file__} : BNGPlotter._datplot()",
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

        self.logger.debug(
            f"Saving figure to {self.out}", loc=f"{__file__} : BNGPlotter._datplot()"
        )
        # save the figure
        plt.savefig(self.out)
