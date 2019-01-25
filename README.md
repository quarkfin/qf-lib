# QF Lib Install Guide

## Windows

There are two ways to install the project for Windows. The easy way is to use the `install.ps1` script, which handles all the program requirements. If you don't want to use this script, an alternative method is described in the [Without Script](#without-script) section.

### With Script

* Run the `install.ps1` script in a PowerShell terminal running as Administrator
* Run `pip install .`
* To check if everything installed correctly, check the [Testing](#testing) section.

### Without Script
NOTICE: If possible use precompiled packages (wheels) provided in the `windows_dependencies` directory to install project's dependencies. However the provided wheels are only suitable for Windows (64-bit architecture) with Python 3.6 (64-bit). 

* Download and install [GTK3+](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2017-11-15/gtk3-runtime-3.22.26-2017-11-15-ts-win64.exe)Install GTK3+ (required for generating PDFs). 
* Download and install [Bloomberg C++ SDK](https://software.tech.bloomberg/BLPAPI-Stable-Generic/blpapi_cpp_3.8.18.1-windows.zip):
    * extract the files from the installation archive (zip)
    * create a new environment variable called `BLPAPI_ROOT` and set it to the path of the `/bin` directory inside the Bloomberg's directory (extracted from the `zip` achive)
    * add `/bin` directory to the `PATH` environment variable
* Install Bloomberg Python library by running `python -m pip install --index-url=https://bloomberg.bintray.com/pip/simple blpapi`
* Install `numpy` by running `pip install numpy-1.15.4+mkl-cp36-cp36m-win_amd64.whl` in the `windows_dependencies` directory.
* Install `scipy` by running `pip install scipy-1.1.0-cp36-cp36m-win_amd64.whl` in the `windows_dependencies` directory.
* Install `cvxopt` by running `pip install cvxopt-1.2.2-cp36-cp36m-win_amd64.whl` in the `windows_dependencies` directory.
* Install `pyodbc` by running `pip install pyodbc-4.0.24-cp36-cp36m-win_amd64.whl` in the `windows_dependencies` directory.
* Install `TA Lib`:
    * download [ta-lib-0.4.0-msvc.zip](http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-msvc.zip) and extract it to C:\ta-lib
    * run `pip install TA_Lib-0.4.17-cp36-cp36m-win_amd64.whl` in the `windows_dependencies` directory.
* Install `Haver` by running `Haver-1.1.0-cp36-cp36m-win_amd64.whl` in the `windows_dependencies` directory.
* Install other requirements using `pip`. Run `pip install -r requirements.txt` in the main directory of the `QuantFin Lib`.


#### Links
* `windows_dependencies` directory
* [GTK3+](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2017-11-15/gtk3-runtime-3.22.26-2017-11-15-ts-win64.exe)
* [Bloomberg C++ SDK](https://software.tech.bloomberg/BLPAPI-Stable-Generic/blpapi_cpp_3.8.18.1-windows.zip)
* [Bloomberg Python](https://bintray.com/bloomberg/BLPAPI-Experimental-pip/blpapi_python/3.9.1#files/simple/blpapi)
* [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/)
* [Haver](http://www.haver.com/python/haver/)
* [cvxopt](http://cvxopt.org/install/index.html#windows)

# Testing
After the installation process test that everything was setup fine. In order to do so:
1. Add path of `QuantFin Lib` to the `PYTHONPATH` environment variable (create it if it doesn't exist).
2. Go to the `qf_lib_tests` directory.
3. Run `python run_unit_tests.py` script. There should be no skipped tests and no errors if all the requirements were installed
correctly.
4. Run `python run_integration_tests.py` script. It's better if you have established Bloomberg, Haver and Quandl connections.
Otherwise some tests might be skipped. However there should be no errors.
