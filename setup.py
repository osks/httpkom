import setuptools


with open("README.rst", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='httpkom',
    version='0.19',
    description='REST-like HTTP API for LysKOM',
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
    python_requires='>=3.6',
    install_requires=[
        'pylyskom>=0.6',
        'Flask>=1.1.1',
        'Hypercorn>=0.9.0',
        'six>=1.14.0',
        'Quart>=0.10.0',
    ]
)
