
from setuptools import setup, find_packages
from bionetgen.core.version import get_version

VERSION = get_version()

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
    package_data={'bionetgen': ['templates/*']},
    include_package_data=True,
    entry_points="""
        [console_scripts]
        bionetgen = bionetgen.main:main
    """,
)
