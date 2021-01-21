import os 
import numpy as np
import seaborn as sbrn
import matplotlib.pyplot as plt
from bionetgen.core import BNGResult

class BNGPlotter:
    '''
    Class that does basic plotting for gdat/cdat files
    '''
    def __init__(self, inp, out):
        # read input and output paths
        self.inp = inp
        self.out = out
        # load in the result
        self.result = BNGResult(direct_path=inp)

    def plot(self):
        # get the data out of result object
        path, fname = os.path.split(self.inp)
        fnoext, fext = os.path.splitext(fname)
        self.data = self.result.results[fnoext]
        # get species names
        names = self.data.dtype.names
        # loop over and plot them all
        ctr = 0
        for name in names:
            if name == "time": 
                continue
            ax = sbrn.lineplot(self.data["time"], self.data[name], label=name)
            ctr += 1
            # if there are a lot of lines the legend makes 
            # everything unreadable
            if ctr > 5:
                ax.get_legend().remove()
        # labels and title
        _ = plt.xlabel("time")
        _ = plt.ylabel("species")
        _ = plt.title(fnoext)
        # save the figure
        plt.savefig(self.out)
