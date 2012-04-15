import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'Celltone',
    version = '0.1',
    packages = ['celltone', 'tests'],
    entry_points = {
        'console_scripts': [
            'celltone = celltone.celltone:main'
            ]
        },
    install_requires = ['ply>=3.0', 'pyPortMidi>=0.0.3', 'argparse>=1.0'],

    author = 'Andreas Jansson',
    author_email = 'andreas@jansson.me.uk',
    description = ('A simple programming language for generative music composition using cellular automata'),
    license = 'GPL v3',
    keywords = 'music midi composition cellular automata language',
    long_description = read('README.md'),
    url = 'https://github.com/andreasjansson/celltone',
    )
