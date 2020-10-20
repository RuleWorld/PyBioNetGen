
from setuptools import setup, find_packages
from bionetgen.core.version import get_version

VERSION = get_version()

#### BNG DOWNLOAD START ####
# Handle BNG download and inclusion
import platform,json
import urllib.request
# let's pull URLs for each distribution
# in the latest distribution
rls_url = "https://api.github.com/repos/RuleWorld/bionetgen/releases/latest"
rls_resp = urllib.request.urlopen(rls_url)
rls_json_txt = rls_resp.read()
rls_json = json.loads(rls_json_txt)
assets = rls_json['assets']
for asset in assets:
    browser_url = asset['browser_download_url']
    if 'linux' in browser_url:
        linux_url = browser_url
    elif 'mac' in browser_url:
        mac_url = browser_url
    elif 'win' in browser_url:
        windows_url = browser_url

# next set the correct URL for platform
# system = platform.system() 
# if system == "Linux":
#     bng_url = linux_url
# elif system == "Windows":
#     bng_url = windows_url
# elif system == "Darwin":
#     bng_url = mac_url
# else:
#     print("Setup doesn't know your system! {} \
#             BioNetGen won't be installed".format(system))
#     bng_url = None

# next download and place the appropriate files
bng_downloaded = False
# for bng_url in [linux_url, mac_url, windows_url]:
for iurl, bng_url in enumerate([linux_url, mac_url]):
    # if bng_url is not None:

    # this lists the stuff in bng distribution 
    # to move in our python package
    to_move = ["BNG2.pl", "bin", "Perl2", "VERSION"]
    # import file and download libraries
    import os,shutil
    ext = bng_url.split(".")[-1]
    fname = "bng.{}".format(ext)
    # download bng distro
    urllib.request.urlretrieve(bng_url, fname)
    # file extension dependent actions, tar for 
    # mac and linux, zip for windows
    if "tgz" == ext or "gz" == etx:
        import tarfile
        bng_arch = tarfile.open(fname)
        fold_name = bng_arch.getnames()[0]
        bng_arch.extractall()
        # make sure bionetgen/bng exists
        if iurl == 0:
            bng_path_to_move = "bionetgen/bng-linux"
        elif iurl == 1:
            bng_path_to_move = "bionetgen/bng-mac"

        if os.path.isdir(bng_path_to_move):
            shutil.rmtree(bng_path_to_move)
        os.mkdir(bng_path_to_move)
        # move items in
        for item in to_move:
            shutil.move(os.path.join(fold_name, item), os.path.join(bng_path_to_move, "."))
        # we got bionetgen in
        bng_downloaded = True
        # Done unpacking, remove useless files
        os.remove(fname)
        shutil.rmtree(fold_name)
    elif "zip" == etx:
        import zipfile
        # TODO: handle zip/windows case

if bng_downloaded:
    # TODO: only add if not there
    with open("MANIFEST.in", "a") as f:
        f.write("recursive-include bionetgen/bng-linux *\n")
        f.write("recursive-include bionetgen/bng-mac *\n")
#### BNG DOWNLOAD DONE ####

f = open('README.md', 'r')
LONG_DESCRIPTION = f.read()
f.close()

setup(
    name='bionetgen',
    version=VERSION,
    description='A simple CLI for BioNetGen ',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Ali Sinan Saglam',
    author_email='als251@pitt.edu',
    url='https://github.com/ASinanSaglam/BNG_cli',
    license='unlicensed',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'bionetgen': ['bng/*']},
    zip_safe=False,
    include_package_data=True,
    entry_points="""
        [console_scripts]
        bionetgen = bionetgen.main:main
    """,
)
