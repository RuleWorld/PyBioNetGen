import os
import numpy as np


class BNGResult:
    """
    Class that loads in gdat/cdat/scan files

    Usage: BNGResult(path="/path/to/folder") OR
           BNGResult(direct_path="/path/to/file.gdat")

    Arguments
    ---------
    path : str
        path that points to a folder containing files to be
        loaded by the class
    direct_path : str
        path that directly points to a file to load

    Methods
    -------
    load(fpath)
        loads in the direct path to the file and returns
        numpy.recarray
    """

    def __init__(self, path=None, direct_path=None):
        # TODO Make it so that with path you can supply an
        # extension or a list of extensions to load in
        self.gdats = {}
        self.cdats = {}
        self.scans = {}
        self.cnames = {}
        self.snames = {}
        self.gnames = {}
        if direct_path is not None:
            path, fname = os.path.split(direct_path)
            fnoext, fext = os.path.splitext(fname)
            self.direct_path = direct_path
            self.file_name = fnoext
            self.file_extension = fext
            self.gnames[fnoext] = direct_path
            self.gdats[fnoext] = self.load(direct_path)
        elif path is not None:
            # TODO change this pattern so that each method
            # is stand alone and usable.
            self.path = path
            self.find_dat_files()
            self.load_results()
        else:
            print(
                "BNGResult needs either a path or a direct path kwarg to load gdat/cdat/scan files from"
            )

    def __repr__(self) -> str:
        s = f"gdats from {len(self.gdats)} models: "
        for r in self.gdats.keys():
            s += f"{r}"
        if len(self.cdats) > 0:
            s += f"\ncdats from {len(self.cdats)} models: "
            for r in self.cdats.keys():
                s += f"{r}"
        if len(self.scans) > 0:
            s += f"\nscans from {len(self.scans)} models: "
            for r in self.scans.keys():
                s += f"{r}"
        return s

    def __getitem__(self, key):
        if isinstance(key, int):
            k = list(self.gdats.keys())[key]
            it = self.gdats[k]
        else:
            it = self.gdats[key]
        return it

    def __iter__(self):
        return self.gdats.__iter__()

    def load(self, fpath):
        path, fname = os.path.split(fpath)
        fnoext, fext = os.path.splitext(fname)
        if fext == ".gdat" or fext == ".cdat":
            return self._load_dat(fpath)
        elif fext == ".scan":
            return self._load_scan(fpath)
        else:
            print("BNGResult doesn't know the file type of {}".format(fpath))
            return None

    def _load_scan(self, fpath):
        return self._load_dat(fpath)

    def find_dat_files(self):
        files = os.listdir(self.path)
        ext = "gdat"
        gdat_files = filter(lambda x: x.endswith(f".{ext}"), files)
        for dat_file in gdat_files:
            name = dat_file.replace(f".{ext}", "")
            self.gnames[name] = dat_file

        ext = "cdat"
        cdat_files = filter(lambda x: x.endswith(f".{ext}"), files)
        for dat_file in cdat_files:
            name = dat_file.replace(f".{ext}", "")
            self.cnames[name] = dat_file

        ext = "scan"
        scan_files = filter(lambda x: x.endswith(f".{ext}"), files)
        for dat_file in scan_files:
            name = dat_file.replace(f".{ext}", "")
            self.snames[name] = dat_file

    def load_results(self):
        # load gdat files
        for name in self.gnames:
            gdat_path = os.path.join(self.path, self.gnames[name])
            self.gdats[name] = self.load(gdat_path)
        # load gdat files
        for name in self.cnames:
            cdat_path = os.path.join(self.path, self.cnames[name])
            self.cdats[name] = self.load(cdat_path)
        # load scan files
        for name in self.snames:
            scan_path = os.path.join(self.path, self.snames[name])
            self.scans[name] = self.load(scan_path)

    def _load_dat(self, path, dformat="f8"):
        """
        This function takes a path to a gdat/cdat file as a string and loads that
        file into a numpy structured array, including the correct header info.
        TODO: Add link

        Optional argument allows you to set the data type for every column. See
        numpy dtype/data type strings for what's allowed. TODO: Add link
        """
        # First step is to read the header,
        # we gotta open the file and pull that line in
        with open(path, "r") as f:
            header = f.readline()
        # Ensure the header info is actually there
        assert header.startswith("#"), "No header line that starts with #"
        # Now turn it into a list of names for our struct array
        header = header.replace("#", "")
        headers = header.split()
        # For a magical reason this is how numpy.loadtxt wants it,
        # in tuples passed as a dictionary with names/formats as keys
        names = tuple(headers)
        formats = tuple([dformat for i in range(len(headers))])
        # return the loadtxt result as a record array
        # which is similar to pandas data format without the helper functions
        return np.rec.array(
            np.loadtxt(path, dtype={"names": names, "formats": formats})
        )
