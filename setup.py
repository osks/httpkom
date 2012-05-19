from setuptools import setup

setup(
    name='httpkom',
    version='0.1',
    long_description=__doc__,
    packages=['httpkom'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask', 'mimeparse', 'Sphinx']
)
