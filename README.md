# QF Lib Install Guide

## Windows

There are two ways to install the project for Windows. The easy way is to use the `install.ps1` script, which handles all the program requirements. If you don't want to use this script, an alternative method is described in the [Without Script](#without-script) section.

### With Script

* Run the `install.ps1` script in a PowerShell terminal running as Administrator
* Run `pip install .`
* To check if everything installed correctly, check the [Testing](#testing) section.

### Without Script

* Download and install [GTK3+](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2017-11-15/gtk3-runtime-3.22.26-2017-11-15-ts-win64.exe) Runtime environment

  * Used for PDF Exporting, but also required for the library to install correctly.

* To use the Bloomberg data provider you must have an active Bloomberg Terminal.

  * Download and install [Bloomberg Python API](https://bloomberg.bintray.com/BLPAPI-Experimental-Generic/:blpapi-3.9.0b1.win-amd64-py3.5.msi)

  * Download [Bloomberg C++ SDK](https://software.tech.bloomberg/BLPAPI-Stable-Generic/blpapi_cpp_3.8.18.1-windows.zip) and extract the zip file. Add the `/bin` file to your `PATH` environment variable. Also create a new environment variable called `BLPAPI_ROOT`, and add the `/bin` folder.

* To use the Haver data provider you must have access to Haver Analytics data.

  * Download and install the [Haver](http://www.haver.com/python/haver/) wheel.

* To use most Portfolio Models from Portfolio Construction module, you will need to [install cvxopt](http://cvxopt.org/install/index.html#windows)

# Testing

To ensure all programs and project requirements have installed correctly, run `python -m unittest discover -s qf_tests -p 'test_*'` command in the root directory. All tests should pass. A few tests might be skipped based on your connection to certain data providers.
