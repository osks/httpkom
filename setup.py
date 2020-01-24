import setuptools

from httpkom.version import __version__


with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='httpkom',
    version=__version__,
    description='REST-like API for LysKOM',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author='Oskar Skoog',
    author_email='oskar@osd.se',
    url='https://github.com/osks/httpkom',
    packages=['httpkom'],
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
    ],
    include_package_data=True,
    zip_safe=False,
    #python_requires='>=2.7, >=3.7',
    install_requires=[
        'Flask',
        'mimeparse',
        'Sphinx',
        'pylyskom',
        'six',
        'CherryPy',
        'Paste'
    ]
)
