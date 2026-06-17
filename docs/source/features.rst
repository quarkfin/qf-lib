========
Features
========


QF-Lib is a Python library that provides high quality tools for quantitative finance. Among the
features, there are modules for portfolio construction, time series analysis, risk monitoring and a
diverse charting package. The library allows analyzing financial data in a convenient way, while
providing a wide variety of tools for data processing and presentation of the results.

QF-Lib is a convenient environment for conducting your own analysis. The results will be presented in
a practical form and include a number of charts and statistical measures.

An extensive part of the project is dedicated to backtesting investment strategies. The backtester
uses an **event-driven architecture** and simulates events such as daily market opening or closing.
Thanks to the architecture based on interfaces, it is easy to introduce custom settings. Tested
strategies can consist of different alpha models, position-sizing techniques, risk management settings
and can specify commission pricing or slippage models. After testing a strategy on historical data,
you can put it into a trading environment without modifications.

.. _a-powerful-event-driven-backtester:

A powerful, event-driven backtester
------------------------------------

A large part of the project is dedicated to backtesting investment strategies. The backtester uses an
**event-driven architecture** and simulates events such as daily market opening or closing. It is
designed to **test and evaluate any custom investment strategy**.

**Tech specs**

* Modular design (alpha models, risk management, position sizing)
* Easy to build custom strategies
* Tools to prevent look-ahead bias
* Detailed summary of the backtest
* Deploy strategies on testing or production environments

**Applications**

* Financial engineering
* Investment strategy development, evaluation and testing
* Risk management
* Financial analysis
* Verification of investment ideas

.. raw:: html

   <div class="qf-gallery">
     <img src="_static/images/about/backtester-example-1.png" alt="Backtester example chart" />
     <img src="_static/images/about/backtester-example-2.png" alt="Backtester example chart" />
     <img src="_static/images/about/backtester-example-3.png" alt="Backtester example chart" />
   </div>

Start with :doc:`tutorials/first_strategy_backtest` or read :doc:`reference/backtest_flow`.

.. _multi-tool-for-any-financial-research:

Multi-tool for any financial research
--------------------------------------

QF-Lib provides tools for portfolio construction, time series analysis, and risk monitoring. It
allows analysing financial data in a convenient way and provides a wide variety of tools to process
data and to present the results.

**Tech specs**

* Flexible data sourcing (Bloomberg, Yahoo Finance, Alpaca, CSV, Quandl, and more)
* Adapted data containers (based on Pandas)
* Rich charting package
* Export to Excel, PDF, or email notifications

**Applications**

* Financial analysis
* Building custom market indicators
* Financial products evaluation
* Portfolio construction
* Risk management
* Academic research
* Time series analysis

.. raw:: html

   <div class="qf-gallery">
     <img src="_static/images/about/multi-tool-example-1.png" alt="Multi-tool example" />
     <img src="_static/images/about/multi-tool-example-2.png" alt="Multi-tool example" />
     <img src="_static/images/about/multi-tool-example-3.png" alt="Multi-tool example" />
   </div>

See :doc:`tutorials/portfolio_construction_tutorial`, :doc:`api_docs/plotting`, and :doc:`api_docs/data_providers`.

Examples of backtest reports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After a backtest completes, QF-Lib generates tearsheets, portfolio analysis sheets, and trade
statistics.

.. raw:: html

   <div class="qf-gallery">
     <img src="_static/images/about/backtest-report-1.png" alt="Backtest report example" />
     <img src="_static/images/about/backtest-report-2.png" alt="Backtest report example" />
   </div>

Walkthrough: :doc:`tutorials/analysing_backtest_results`.

Key capabilities
~~~~~~~~~~~~~~~~

**Flexible data sourcing**
    Choose Bloomberg, Yahoo Finance, Alpaca, CSV, Quandl, Haver, Portara, and other providers.
    Extend the ``DataProvider`` interface for custom sources; preload data to speed up research runs.

**Look-ahead bias protection**
    Wrap providers with a data handler so backtests never see future bars.

**Adapted data containers**
    Time-indexed 1D/2D/3D structures for prices, returns, and log returns with straightforward
    casting from Pandas.

**Summary generation**
    Export studies to PDF, Excel, or HTML. See :doc:`api_docs/document_utils`.

Project history
~~~~~~~~~~~~~~~

QF-Lib is maintained by the **CERN Pension Fund** and is available under :doc:`license`. See
:doc:`release_notes` for version history.

Get started
~~~~~~~~~~~

.. raw:: html

   <div class="qf-get-started">
     <a class="qf-feature-card" href="getting_started.html">
       <p><strong>Installation</strong></p>
       <p>Install QF-Lib, optional data providers, and <code>settings.json</code>.</p>
       <span class="qf-card-cta">Getting started →</span>
     </a>
     <a class="qf-feature-card" href="tutorials.html">
       <p><strong>Tutorials</strong></p>
       <p>Backtesting, alpha models, data providers, and portfolio construction.</p>
       <span class="qf-card-cta">Tutorials →</span>
     </a>
     <a class="qf-feature-card" href="api_reference.html">
       <p><strong>API reference</strong></p>
       <p>Auto-generated module and class reference.</p>
       <span class="qf-card-cta">API Reference →</span>
     </a>
     <a class="qf-feature-card" href="contact.html">
       <p><strong>Community</strong></p>
       <p>Questions and collaboration on Discord.</p>
       <span class="qf-card-cta">Contact us →</span>
     </a>
   </div>


Flexible data sourcing
----------------------

The project supports an easy selection of the data source. It currently provides financial data from
Bloomberg, Yahoo Finance, Alpaca, Quandl, Haver Analytics, Portara, Binance, Interactive Brokers,
and CSV files. The ``DataProvider`` interface can be extended for any other source. For complex
computations, operation time can be reduced using data preloading. Data structures can be cached to
avoid excess requests when tests run multiple times. Incomplete data can be cleaned - for example
using regression.

See :doc:`api_docs/data_providers`.

Tools to prevent look-ahead bias
--------------------------------

All ``DataProvider`` types (including custom ones) can be wrapped with a ``DataHandler``, usable in
both live and backtest environments. It ensures data from the future is not passed into testing
components - essential in the backtester.

Adapted data containers
-----------------------

QF-Lib introduces custom time-indexed data structures for prices, returns, and log returns. The
structures are 1-, 2-, and 3-dimensional and simplify conversion between data types. Any
time-indexed pandas ``DataFrame`` or ``Series`` can be cast using ``cast_dataframe`` and
``cast_series``.

See :doc:`api_docs/containers`.

Summary generation
------------------

Studies can be summarised in practical documents with charts, financial statistics tables, and
custom sections. Supported formats include PDF, Microsoft Excel, and HTML. Documents can be
published automatically to configured e-mail addresses.

See :doc:`api_docs/document_utils` and :doc:`tutorials/analysing_backtest_results`.

Simple adjustment and extensibility
-------------------------------------

The architecture supports miscellaneous tests and studies. QF-Lib works as a financial multi-tool for
developers who want to facilitate research while keeping full control over custom logic.
