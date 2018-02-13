# IMOS Compliance Checker Plugin

[![Build Status](https://travis-ci.org/aodn/cc-plugin-imos.png?branch=master)](https://travis-ci.org/aodn/cc-plugin-imos)

This is a checker for compliance with the [IMOS NetCDF Conventions](https://s3-ap-southeast-2.amazonaws.com/content.aodn.org.au/Documents/IMOS/Conventions/IMOS_NetCDF_Conventions.pdf).

It works with the [ioos/compliance-checker](https://github.com/ioos/compliance-checker).


## Installation

Clone the repository:
```bash
git clone git@github.com:aodn/cc-plugin-imos.git
```

Create a virtual environment and install the plugin (which installs the core checker as a dependency):
```bash
cd cc-plugin-imos
mkdir env
virtualenv env/cc-plugin-imos
source env/cc-plugin-imos/bin/activate
pip install -e .
```

## Testing

```bash
python setup.py test -s cc_plugin_imos.tests
```


## Usage

`compliance-checker -t=imos file.nc`

Run `compliance-checker -h` for help on command-line options.
