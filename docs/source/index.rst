QF-Lib Guide
************************************

**QF-Lib** is a Python library that provides high quality tools for quantitative finance.
A large part of the project is dedicated to backtesting investment strategies.
The Backtester uses an **event-driven architecture** and simulates events such as daily market opening
or closing. It is designed to **test and evaluate any custom investment strategy**. For more details check the `Projects
Website`_.

.. _Projects Website: https://quarkfin.github.io/qf-lib-info

Getting started
-----------------
:doc:`installation`
    How to install this library.

:doc:`configuration`
    Library configuration and customization options.

Backtesting
------------

:doc:`backtesting`
    Code of the Backtester, which uses an event-driven architecture.

:doc:`data_providers`
    Data providers whose purpose is to download the financial data from various vendors such as Bloomberg or Quandl.

:doc:`containers`
    Data structures that extend the functionality of pandas Series, pandas DataFrame and numpy DataArray containers and facilitate the computations performed on time-indexed structures of prices or price returns.

:doc:`common`
    Various generic tools.

Analysis
---------

:doc:`analysis`
    Analyze strategy progress and generate files containing the analysis results

:doc:`plotting`
    Chart templates along with some easy-to-use decorators.

:doc:`document_utils`
    Templates, styles and components used to export the results and save them.

:doc:`indicators`
    Market indicators that can be implemented in strategies or used for the analysis.

:doc:`portfolio_construction`
    Components which facilitate the process of portfolio construction. The construction process involves covariance matrix optimization with one of the implemented optimizers.



.. Hidden TOCs
.. toctree::
   :caption: Getting started
   :maxdepth: 1
   :hidden:

   installation
   configuration

.. toctree::
   :caption: Backtesting
   :maxdepth: 2
   :hidden:

   backtesting
   data_providers
   containers
   common

.. toctree::
   :caption: Analysis
   :maxdepth: 2
   :hidden:

   analysis
   plotting
   document_utils
   indicators
   portfolio_construction


Indices and tables
==================

* :ref:`genindex`
