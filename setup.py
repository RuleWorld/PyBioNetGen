from setuptools import setup, find_packages
from bionetgen.core.version import get_version
import itertools as itt

VERSION = get_version()

#### BNG DOWNLOAD START ####
# Handle BNG download and inclusion
import time,json
import urllib.request
# let's pull URLs for each distribution
# in the latest distribution
rls_url = "https://api.github.com/repos/RuleWorld/bionetgen/releases/latest"
# sometimes we exceed the rate, we want to 
# ensure this doesn't happen, ever
time.sleep(5)
rls_resp = urllib.request.urlopen(rls_url)
rls_json_txt = rls_resp.read()
rls_json = json.loads(rls_json_txt)
# write BNG version tag to use later in banner
bng_version_tag = rls_json['tag_name']
with open("bionetgen/assets/BNGVERSION", 'w') as f:
    f.write(bng_version_tag)
# get assests
assets = rls_json['assets']
for asset in assets:
    browser_url = asset['browser_download_url']
    if 'linux' in browser_url:
        linux_url = browser_url
    elif 'mac' in browser_url:
        mac_url = browser_url
    elif 'win' in browser_url and "tgz" in browser_url:
        windows_url = browser_url

# next download and place the appropriate files
import os,shutil,tarfile,zipfile
bng_downloaded = False
for iurl,bng_url in enumerate([linux_url, mac_url, windows_url]):
    # this lists the stuff in bng distribution 
    # to move in our python package
    if iurl < 2:
        to_move = [["BNG2.pl"], ["bin","NFsim"], ["bin", "run_network"], ["bin","sundials-config"], ["Perl2"], ["VERSION"]]
    elif iurl == 2:
        to_move = [["BNG2.pl"], ["bin","NFsim.exe"], ["bin", "run_network.exe"], ["bin","sundials-config"], ["Perl2"], ["VERSION"], ["bin","cyggcc_s-seh-1.dll"],["bin","cygstdc++-6.dll"],["bin","cygwin1.dll"],["bin","cygz.dll"],["bin","libgcc_s_dw2-1.dll"],["bin","libstdc++-6.dll"]]
    # import file and download libraries
    ext = bng_url.split(".")[-1]
    fname = "bng.{}".format(ext)
    # download bng distro
    urllib.request.urlretrieve(bng_url, fname)
    # file extension dependent actions, tar for 
    # mac and linux, zip for windows
    if iurl < 2:
    # if "tgz" == ext or "gz" == etx:
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
        os.mkdir(os.path.join(bng_path_to_move, "bin"))
        # move items in
        for item in to_move:
            item_list = [fold_name] + item
            item_path = list(itt.accumulate(item_list, lambda x,y: os.path.join(x,y)))[-1]
            to_move_item = [bng_path_to_move] + item
            to_move_path = list(itt.accumulate(to_move_item, lambda x,y: os.path.join(x,y)))[-1]
            shutil.move(item_path, to_move_path)
        # we got bionetgen in
        bng_downloaded = True
        # Done unpacking, remove useless files
        bng_arch.close()
        os.remove(fname)
        shutil.rmtree(fold_name)
    if iurl == 2:
    # elif "zip" == etx:
        # TODO: handle zip/windows case
        # bng_arch = zipfile.Zipfile(fname)
        # fold_name = bng_arch.namelist()[0]
        # bng_arch.extractall()
        bng_arch = tarfile.open(fname)
        fold_name = bng_arch.getnames()[0]
        bng_arch.extractall()
        # bng folder
        if iurl == 2:
            bng_path_to_move = "bionetgen/bng-win"

        if os.path.isdir(bng_path_to_move):
            shutil.rmtree(bng_path_to_move)
        os.mkdir(bng_path_to_move)
        os.mkdir(os.path.join(bng_path_to_move, "bin"))
        # move items in
        for item in to_move:
            item_list = [fold_name] + item
            item_path = list(itt.accumulate(item_list, lambda x,y: os.path.join(x,y)))[-1]
            to_move_item = [bng_path_to_move] + item[:-1]
            to_move_path = list(itt.accumulate(to_move_item, lambda x,y: os.path.join(x,y)))[-1]
            shutil.move(item_path, to_move_path)
        # we got bionetgen in
        bng_downloaded = True
        # Done unpacking, remove useless files
        bng_arch.close()
        os.remove(fname)
        shutil.rmtree(fold_name)

# if bng_downloaded:
#     # TODO: only add if not there
#     with open("MANIFEST.in", "a") as f:
#         f.write("recursive-include bionetgen/bng-linux *\n")
#         f.write("recursive-include bionetgen/bng-mac *\n")
#         f.write("recursive-include bionetgen/bng-win *\n")
#### BNG DOWNLOAD DONE ####

with open('README.md', 'r') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='bionetgen',
    version=VERSION,
    description='A simple CLI and library for BioNetGen modelling language',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author='Ali Sinan Saglam',
    author_email='als251@pitt.edu',
    url='https://github.com/RuleWorld/PyBioNetGen',
    license='unlicensed',
    packages=find_packages(exclude=['ez_setup', 'tests*']),
    package_data={'bionetgen': ['bng*/*', 'assets/*']},
    zip_safe=False,
    include_package_data=True,
    entry_points="""
        [console_scripts]
        bionetgen = bionetgen.main:main
    """,
    install_requires=[
        "cement",
        "nbopen",
        "numpy",
        "pyyaml",
        "colorlog",
        "xmltodict",
        "seaborn",
    ]
)
