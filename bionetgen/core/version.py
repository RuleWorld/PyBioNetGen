import os
from cement.utils.version import get_version as cement_get_version

# Find VERSION file
vpath = os.path.abspath(__file__)
vpath = os.path.dirname(vpath)
vpath = vpath.split(os.path.sep)
vpath = os.path.sep.join(vpath[:-2])
vpath = os.path.join(vpath, "VERSION")
with open(vpath, "r") as f:
    v = f.read()
vtuple = [0, 0, 0, 0, 0]
for iv, ver in enumerate(v.split()):
    try:
        vtuple[iv] = int(ver)
    except:
        vtuple[iv] = ver

VERSION = tuple(vtuple)


def get_version(version=VERSION):
    return cement_get_version(version)
