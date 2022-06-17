# QF-Lib

[![PyPI](https://img.shields.io/pypi/v/qf-lib?color=green&label=PyPI%20Latest%20Release)](https://pypi.org/project/qf-lib/)
[![Downloads](https://static.pepy.tech/personalized-badge/qf-lib?period=month&units=international_system&left_color=grey&right_color=blue&left_text=PyPI%20Downloads%20/%20month)](https://pepy.tech/project/qf-lib)
[![GitHub](https://img.shields.io/github/license/quarkfin/qf-lib?color=orange&label=License)](https://github.com/quarkfin/qf-lib/blob/master/LICENSE)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/qf-lib?color=yellow&label=python)
[![Codecov](https://img.shields.io/codecov/c/gh/quarkfin/qf-lib?color=pink)](https://app.codecov.io/gh/quarkfin/qf-lib)
[![Documentation Status](https://readthedocs.org/projects/qf-lib/badge/)](https://qf-lib.readthedocs.io/)
[![CI](https://github.com/quarkfin/qf-lib/actions/workflows/tests.yml/badge.svg?branch=master)](https://github.com/quarkfin/qf-lib/actions/workflows/tests.yml)
![PyPI - Format](https://img.shields.io/pypi/format/qf-lib?color=lightgrey)
![PyPI - Status](https://img.shields.io/pypi/status/qf-lib?color=darkred)

## What is QF-lib?
**QF-Lib** is a Python library that provides high quality tools for quantitative finance. 
A large part of the project is dedicated to backtesting investment strategies. 
The Backtester uses an **event-driven architecture** and simulates events such as daily market opening 
or closing. It is designed to **test and evaluate any custom investment strategy**.

Main features include:
* Flexible data sourcing - the project supports the possibility of an easy selection of the data source. Currently provides financial data from **Bloomberg**, **Quandl**, **Haver Analytics** or **Portara**. To check if there are any additional dependencies necessary for any of these data providers please visit [the installation guide](https://qf-lib.readthedocs.io/en/latest/installation.html#installing-optional-data-providers).
* Tools to prevent look-ahead bias in the backtesting environment.
* Adapted [data containers](https://qf-lib.readthedocs.io/en/latest/reference/structure.html#containers), which extend the functionality of pandas `Series'` and `Dataframes`.
* Summary generation - all performed studies can be summarized with a practical and informative document explaining the results. [Several document templates](https://qf-lib.readthedocs.io/en/latest/reference/structure.html#analysis) are available in the project.
* Simple adjustment of existing settings and creation of new functionalities.


## Installation
You can install `qf-lib` using the pip command:

```sh
pip install qf-lib
```
 
Alternatively, to install the library from sources, you can download the project and in the qf_lib directory 
(same one where you found this file after cloning the repository) execute the following command:

```sh
python setup.py install
```

## Prerequisites
The library uses [WeasyPrint](https://weasyprint.readthedocs.io) to export documents to PDF. WeasyPrint requires additional dependencies, check the 
[platform-specific instructions for Linux, macOS and Windows installation](https://weasyprint.readthedocs.io/en/stable/install.html).

In order to facilitate the GTK3+ installation process for Windows you can use 
[following installers](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases). Download and run the latest 
`gtk3-runtime-x.x.x-x-x-x-ts-win64.exe` file to install the GTK3+.

## Documentation
* Installation guide: https://qf-lib.readthedocs.io/en/latest/installation.html
* Configuration guide: https://qf-lib.readthedocs.io/en/latest/configuration.html
* API documentation: https://qf-lib.readthedocs.io/
