=============
API Reference
=============

This section documents the public Python API of QF-Lib. Each page lists classes and
functions for one package, generated automatically from docstrings.

Use the module index below to jump directly to a package. For narrative explanations
and worked examples, see :doc:`tutorials`.

Modules
-------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Module
     - Description
   * - :doc:`backtesting`
     - Event-driven backtester: strategies, orders, portfolio, execution, and trading session.
   * - :doc:`data_providers`
     - Market data adapters (CSV, Bloomberg, Quandl, YFinance, Alpaca, and others).
   * - :doc:`containers`
     - Typed pandas and xarray wrappers for prices, returns, and futures data.
   * - :doc:`common`
     - Tickers, enums, date utilities, return and risk ratios, factorisation helpers.
   * - :doc:`analysis`
     - Tearsheets, timeseries and trade analysis, signals plotting, overfitting tools.
   * - :doc:`plotting`
     - Chart classes, decorators, and plotting helpers built on Matplotlib.
   * - :doc:`document_utils`
     - PDF, HTML, and Excel export utilities for reports and results.
   * - :doc:`indicators`
     - Market indicators usable in strategies or standalone analysis.
   * - :doc:`portfolio_construction`
     - Portfolio optimisers and weighting models (Min-Variance, Risk Parity, Black-Litterman).

.. toctree::
   :maxdepth: 2
   :hidden:

   backtesting
   data_providers
   containers
   common
   analysis
   plotting
   document_utils
   indicators
   portfolio_construction
