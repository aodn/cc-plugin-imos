from __future__ import with_statement

from setuptools import find_packages, setup

from cc_plugin_imos import __version__


def readme():
    with open('README.md') as f:
        return f.read()


reqs = [line.strip() for line in open('requirements.txt')]

setup(name                 = "cc_plugin_imos",
      version              = __version__,
      description          = "Compliance Checker plugin for IMOS conventions",
      long_description     = readme(),
      license              = 'GPLv3',
      author               = "Xiao Ming Fu, Marty Hidas",
      author_email         = "Marty.Hidas@utas.edu.au",
      url                  = "https://github.com/aodn/data-services.git",
      packages             = find_packages(),
      install_requires     = reqs,
      classifiers          = [
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: Scientific/Engineering',
      ],
      entry_points         = {
          'compliance_checker.suites': [
              'imos13 = cc_plugin_imos.imos:IMOS1_3Check',
              'imos14 = cc_plugin_imos.imos:IMOS1_4Check',
              'ghrsst = cc_plugin_imos.srs:IMOSGHRSSTCheck'
          ]
      },
      package_data         = {
          'cc_plugin_imos': ['tests/data/*.cdl']
      }
     )
