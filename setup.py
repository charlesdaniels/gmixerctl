#!/usr/bin/env python

from gmixerctl import constants as constants 
from setuptools import setup
from setuptools import find_packages

short_description = \
    'GUI Wrapper for OpenBSD\'s mixerctl'

long_description = '''
'''.lstrip()  # remove leading newline

classifiers = [
    # see http://pypi.python.org/pypi?:action=list_classifiers
    ]

setup(name="gmixerctl",
      version=constants.version,
      description=short_description,
      long_description=long_description,
      author="Charles Daniels",
      author_email="cdaniels@fastmail.com",
      url="https://github.com/charlesdaniels/gmixerctl",
      license='BSD',
      classifiers=classifiers,
      keywords='',
      packages=find_packages(),
      entry_points={'console_scripts':
                    ['gmixerctl=gmixerctl.gui:main']},
      package_dir={'gmixerctl': 'gmixerctl'},
      platforms=['POSIX']
      )
