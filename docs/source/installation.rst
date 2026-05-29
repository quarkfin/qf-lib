Installation
=============
This document will guide you through the installation process and will help you configure the library for the newest release.

You can install the library using the pip command:

.. code:: console

    $ pip install qf-lib


Alternatively, to install the library from sources, you can download the project and in the qf_lib directory (same one where you found this file after cloning the repository) execute the following command:

.. code:: console

    $ python setup.py install

Prerequisites
--------------

QF-Lib supports the Python versions declared on PyPI:

.. image:: https://img.shields.io/pypi/pyversions/qf-lib
   :alt: Supported Python versions on PyPI

The library has been tested on Windows, macOS, and Ubuntu.

The library uses `WeasyPrint <https://weasyprint.readthedocs.io>`__ to
export documents to PDF. WeasyPrint requires additional dependencies,
check the `platform-specific instructions for Linux, macOS and Windows
installation <https://weasyprint.readthedocs.io/en/stable/install.html>`__.

In order to facilitate the GTK3+ installation process for Windows you
can use `following
installers <https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases>`__.
Download and run the latest ``gtk3-runtime-x.x.x-x-x-x-ts-win64.exe``
file to install the GTK3+.



Installing optional data providers
------------------------------------

The core installation already includes the common built-in providers (for example ``CSVDataProvider`` and
``PortaraDataProvider``). The table below summarises providers that require extra setup.

.. list-table::
   :header-rows: 1
   :widths: 30 27 27 16

   * - Data provider
     - Short description
     - Prerequisites
     - Installation command
   * - ``BloombergDataProvider`` (BLPAPI)
     - Direct Bloomberg Terminal/API market data access.
     - Bloomberg Terminal/API access and local Bloomberg runtime.
     - ``pip install --index-url=https://bcms.bloomberg.com/pip/simple/ blpapi``
   * - ``BloombergDLDataProvider``
     - Bloomberg Data License downloader.
     - Bloomberg Data License credentials and account configuration.
     - ``pip install -e ".[bloomberg_dl]"``
   * - ``QuandlDataProvider``
     - Nasdaq Data Link (Quandl) datasets.
     - Quandl API key for most datasets.
     - ``pip install -e ".[quandl]"``
   * - ``YFinanceDataProvider``
     - Yahoo Finance downloader for quick external data usage.
     - None for common public datasets.
     - ``pip install -e ".[yfinance]"``
   * - ``AlpacaDataProvider``
     - Alpaca stocks and crypto data.
     - API key for equities (crypto can be used without key).
     - ``pip install -e ".[alpaca]"``
   * - ``BinanceDataProvider``
     - Binance crypto market data.
     - Optional Binance credentials depending on endpoint usage.
     - ``pip install python-binance``
   * - ``HaverDataProvider``
     - Haver Analytics data access.
     - Licensed Haver SDK and local Haver environment.
     - Install using Haver official instructions.
   * - Interactive Brokers integration
     - Interactive Brokers API support for broker/data workflows.
     - TWS or IB Gateway and official TWS API installation.
     - ``pip install -e ".[interactive brokers]"``

