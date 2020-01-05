from setuptools import setup
from httpkom.version import __version__

setup(
    name='httpkom',
    version=__version__,
    author='Oskar Skoog',
    author_email='oskar@osd.se',
    long_description=__doc__,
    packages=['httpkom'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask', 'mimeparse', 'Sphinx', 'pylyskom', 'six', 'CherryPy', 'Paste']
)
