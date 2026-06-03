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
   * - :doc:`api_docs/backtesting`
     - Event-driven backtester: strategies, orders, portfolio, execution, and trading session.
   * - :doc:`api_docs/data_providers`
     - Market data adapters (CSV, Bloomberg, Quandl, YFinance, Alpaca, and others).
   * - :doc:`api_docs/containers`
     - Typed pandas and xarray wrappers for prices, returns, and futures data.
   * - :doc:`api_docs/common`
     - Tickers, enums, date utilities, return and risk ratios, factorisation helpers.
   * - :doc:`api_docs/analysis`
     - Tearsheets, timeseries and trade analysis, signals plotting, overfitting tools.
   * - :doc:`api_docs/plotting`
     - Chart classes, decorators, and plotting helpers built on Matplotlib.
   * - :doc:`api_docs/document_utils`
     - PDF, HTML, and Excel export utilities for reports and results.
   * - :doc:`api_docs/indicators`
     - Market indicators usable in strategies or standalone analysis.
   * - :doc:`api_docs/portfolio_construction`
     - Portfolio optimisers and weighting models (Min-Variance, Risk Parity, Black-Litterman).

.. toctree::
   :maxdepth: 2
   :hidden:

   api_docs/backtesting
   api_docs/data_providers
   api_docs/containers
   api_docs/common
   api_docs/analysis
   api_docs/plotting
   api_docs/document_utils
   api_docs/indicators
   api_docs/portfolio_construction
