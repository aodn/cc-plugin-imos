from __future__ import with_statement

from __future__ import absolute_import
from setuptools import find_packages, setup

from cc_plugin_imos import __version__
from io import open


def readme():
    with open('README.md') as f:
        return f.read()


INSTALL_REQUIRES = [
    'compliance-checker',
    'netCDF4>=1.2.4'
]

setup(
    name="cc_plugin_imos",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description="Compliance Checker plugin for IMOS conventions",
    long_description=readme(),
    license='GPLv3',
    author="Xiao Ming Fu, Marty Hidas",
    author_email="Marty.Hidas@utas.edu.au",
    url="https://github.com/aodn/cc-plugin-imos.git",
    packages=find_packages(),
    install_requires=INSTALL_REQUIRES,
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'Intended Audience :: Science/Research',
      'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
      'Operating System :: POSIX :: Linux',
      'Programming Language :: Python',
      'Topic :: Scientific/Engineering',
    ],
    entry_points={
      'compliance_checker.suites': [
          'imos13 = cc_plugin_imos.imos:IMOS1_3Check',
          'imos14 = cc_plugin_imos.imos:IMOS1_4Check',
          'ghrsst = cc_plugin_imos.srs:IMOSGHRSSTCheck'
      ]
    },
    package_data={
      'cc_plugin_imos': ['tests/data/*.cdl']
    }
)
