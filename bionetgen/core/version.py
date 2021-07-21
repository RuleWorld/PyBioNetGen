import os
from cement.utils.version import get_version as cement_get_version

# Find VERSION file
vpath = os.path.dirname(os.path.abspath(__file__))
vpath = os.path.split(vpath)[0]
vpath = os.path.join(*[vpath, "assets", "VERSION"])
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
