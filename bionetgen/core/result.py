import os 
import numpy as np

class BNGResult:
    '''
    Class that loads in gdat files found in a folder
    '''
    def __init__(self, path):
        self.path = path
        self.results = {}
        self.names = {} 
        self.find_gdat_files() 
        self.load_results()

    def find_gdat_files(self):
        files = os.listdir(self.path)
        gdat_files = filter(lambda x: x.endswith(".gdat"), files)
        for gdat_file in gdat_files:
            name = gdat_file.replace(".gdat", "")
            self.names[name] = gdat_file

    def load_results(self):
        for name in self.names: 
            gdat_path = os.path.join(self.path, self.names[name])
            self.results[name] = self.load_gdat(gdat_path)

    def load_gdat(self, path, dformat="f8"):
        '''
        This function takes a path to a gdat/cdat file as a string and loads that 
        file into a numpy structured array, including the correct header info.
        TODO: Add link
    
        Optional argument allows you to set the data type for every column. See
        numpy dtype/data type strings for what's allowed. TODO: Add link
        '''
        # First step is to read the header, 
        # we gotta open the file and pull that line in
        f = open(path)
        header = f.readline()
        f.close()
        # Ensure the header info is actually there
        assert header.startswith("#"), "No header line that starts with #"
        # Now turn it into a list of names for our struct array
        header = header.replace("#","")
        headers = header.split()
        # For a magical reason this is how numpy.loadtxt wants it, 
        # in tuples passed as a dictionary with names/formats as keys
        names = tuple(headers)
        formats = tuple([dformat for i in range(len(headers))])
        # return the loadtxt result as a record array
        # which is similar to pandas data format without the helper functions
        return np.rec.array(np.loadtxt(path, dtype={'names': names, 'formats': formats}))
