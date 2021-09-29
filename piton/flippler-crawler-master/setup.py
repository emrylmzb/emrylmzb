from setuptools import setup, find_packages
from adboox import __version__

setup(
    name='adboox',
    version=__version__,
    packages=find_packages(),
    entry_points={'scrapy': ['settings = adboox.settings']},
    package_data={'adboox': ['data/*']},
)
