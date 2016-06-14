#!/usr/bin/env python
from setuptools import setup, find_packages
import functools
import os
import platform

_PYTHON_VERSION = platform.python_version()
_in_same_dir = functools.partial(os.path.join, os.path.dirname(__file__))

with open(_in_same_dir('irrigationbone', "__version__.py")) as version_file:
            exec(version_file.read()) # pylint: disable=W0122

project_name='irrigationbone'

package_data=[]
for f in os.listdir(project_name):
  if os.path.isfile(os.path.join(project_name,f)):
    if not f.endswith('.py') and not f.endswith('.pyc'):
      package_data.extend( [f] )

"""
package_data.extend( ['sd_reference.txt'] )

with open('packages.json', 'w') as f:
  json.dump( find_packages(), f )

with open('package_data', 'w') as f:
  for s in package_data:
        f.write(s + '\n')
"""

setup(name=project_name,
      classifiers=[
                  "Programming Language :: Python :: 2.7",
                  "Programming Language :: Python :: 3.4",
      ],
      description='Irrigation based on evaporation data',
      author='Niv Gal Waizer',
      author_email='nivw2008@fastmail.fm',
      version=__version__, # pylint: disable=E0602
      url='https://github.com/nivw/irrigation_bone',
      packages=find_packages(exclude=["tests"]),
      install_requires = ['munch>=2.0.4','requests>=2.9.1','logbook','bs4'],
      entry_points={
                  'console_scripts': [
                              'schedule_irrigation = {}.schedule_irrigation:main'.format(project_name),
                              'wfs = {}.wfs:main'.format(project_name),                              
                  ]
      },

)
