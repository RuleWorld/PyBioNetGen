import os 
import numpy as np
import seaborn as sbrn
import matplotlib.pyplot as plt
from bionetgen.core import BNGResult

class BNGPlotter:
    '''
    Class that does basic plotting for gdat/cdat files
    '''
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
        path, fname = os.path.split(self.inp)
        fnoext, fext = os.path.splitext(fname)

        if fext == ".gdat" or fext == ".cdat": 
            self._datplot()
        elif fext == ".scan":
            self._scanplot()
        else:
            print("File type not recognized, only gdat/cdat and scan files are implemented")
            raise NotImplemented

    def _datplot(self):
        # get the data out of result object
        path, fname = os.path.split(self.inp)
        fnoext, fext = os.path.splitext(fname)
        self.data = self.result.results[fnoext]
        # get species names
        names = self.data.dtype.names
        # loop over and plot them all
        ctr = 0
        ax = None
        for name in names:
            if name == "time": 
                continue
            ax = sbrn.lineplot(x=self.data["time"], y=self.data[name], label=name)
            ctr += 1
            # if there are a lot of lines the legend makes 
            # everything unreadable

        assert ax is not None, "No data columns are found in file {}".format(path)
    
        fax = ax.get_figure().gca()
        if not self.kwargs.get("legend", False):
            fax.legend().remove()
        oxmin,oxmax = fax.get_xlim()
        oymin,oymax = fax.get_ylim()

        xmin = self.kwargs.get("xmin", False) or oxmin
        xmax = self.kwargs.get("xmax", False) or oxmax
        ymin = self.kwargs.get("ymin", False) or oymin
        ymax = self.kwargs.get("ymax", False) or oymax

        fax.set_xlim(xmin,xmax)
        fax.set_ylim(ymin,ymax)
        # labels and title
        _ = plt.xlabel(self.kwargs.get("xlabel") or "time")
        _ = plt.ylabel(self.kwargs.get("ylabel") or "concentration")
        _ = plt.title(self.kwargs.get("title") or fnoext)

        # save the figure
        plt.savefig(self.out)

    def _scanplot(self):
        raise NotImplemented
