########################################
Working with Data Providers
########################################

This tutorial explains how to connect QF-Lib to market data. You will learn:

* The :class:`~qf_lib.data_providers.data_provider.DataProvider` interface and its main methods.
* How to set up a :class:`~qf_lib.data_providers.csv.csv_data_provider.CSVDataProvider` for offline development.
* How to pre-load data with :class:`~qf_lib.data_providers.prefetching_data_provider.PrefetchingDataProvider` for faster backtesting.
* What ``PriceField`` and ``Frequency`` enums represent and when to use each.
* How tickers work in QF-Lib.
* How each built-in provider is used (CSV, prefetch, YFinance, Quandl, Bloomberg, Alpaca, and others).
* Using some real-world data providers.

.. tip::
    Start with :class:`~qf_lib.data_providers.csv.csv_data_provider.CSVDataProvider` while developing a
    strategy, then switch to a vendor provider when you need live or licensed data.

.. note::
    For provider-specific installation prerequisites (dependencies, vendor software, credentials),
    see :doc:`installation`, section ``Installing optional data providers``.



*******************************************************
Data provider architecture
*******************************************************

All data providers implement the abstract
:class:`~qf_lib.data_providers.data_provider.DataProvider` interface. The main methods are:

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Method
     - What it returns
   * - ``get_price(tickers, fields, start_date, end_date)``
     - Adjusted OHLCV (and volume) over a date range. Returns
       :class:`~qf_lib.containers.series.prices_series.PricesSeries` (one ticker, one field),
       :class:`~qf_lib.containers.dataframe.prices_dataframe.PricesDataFrame` (multiple tickers or fields),
       or :class:`~qf_lib.containers.qf_data_array.QFDataArray` (multiple tickers *and* fields).
   * - ``get_history(tickers, fields, start_date, end_date)``
     - Any historical attributes (price columns as strings, fundamentals, custom series). Returns
       :class:`~qf_lib.containers.series.qf_series.QFSeries`,
       :class:`~qf_lib.containers.dataframe.qf_dataframe.QFDataFrame`, or
       :class:`~qf_lib.containers.qf_data_array.QFDataArray` depending on how many tickers and fields you request.
       ``get_price`` is a convenience wrapper around ``get_history`` that maps ``PriceField`` enums to provider columns
       and returns price-specific container types.
   * - ``historical_price(ticker, field, nr_of_bars)``
     - The latest ``nr_of_bars`` bars for one or more tickers and fields. Returns
       :class:`~qf_lib.containers.series.prices_series.PricesSeries` or
       :class:`~qf_lib.containers.dataframe.prices_dataframe.PricesDataFrame` (or
       :class:`~qf_lib.containers.qf_data_array.QFDataArray` in the fully general case). This is the usual call inside
       a running backtest at each bar.

.. note::
    Inside a running backtest, use the session's ``DataProvider`` (accessible as ``ts.data_provider`` or
    ``self.data_provider`` on your strategy). It is wired to the simulation clock so that requests at
    time ``t`` only see data up to and including ``t`` - you do not accidentally use future bars.


*******************************************************
PriceField - OHLCV
*******************************************************

:class:`~qf_lib.common.enums.price_field.PriceField` is an enum that selects one column of bar data:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Value
     - Meaning
   * - ``PriceField.Open``
     - The opening price of the bar.
   * - ``PriceField.High``
     - The highest price reached within the bar.
   * - ``PriceField.Low``
     - The lowest price reached within the bar.
   * - ``PriceField.Close``
     - The closing price of the bar. **Most strategies use this.**
   * - ``PriceField.Volume``
     - The total traded volume for the bar (in units of the asset, not currency).

Usage:

.. code-block:: python

    from qf_lib.common.enums.price_field import PriceField

    # Fetch only close prices
    prices = data_provider.get_price(ticker, PriceField.Close, start_date, end_date)

    # Fetch multiple fields at once - returns a PricesDataFrame
    ohlcv = data_provider.get_price(
        ticker,
        [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close, PriceField.Volume],
        start_date,
        end_date,
    )


*******************************************************
Frequency
*******************************************************

:class:`~qf_lib.common.enums.frequency.Frequency` defines the bar size when you **request** data from a provider.

Backtest session frequency
============================

On :class:`~qf_lib.backtesting.trading_session.backtest_trading_session_builder.BacktestTradingSessionBuilder`,
``set_frequency`` defines how the **backtester** steps through time and computes orders, positions, and P&L. Only
two values are supported:

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Value
     - Role in the backtest
   * - ``Frequency.DAILY``
     - One event cycle per trading day (default for most strategies).
   * - ``Frequency.MIN_1``
     - One event cycle per minute (intraday backtests).

.. code-block:: python

    session_builder.set_frequency(Frequency.DAILY)

Frequency when fetching data
=============================

For **data requests** (``get_price``, ``get_history``, ``historical_price``), you can use many other bar sizes, such as
``Frequency.MIN_5``, ``Frequency.MIN_15``, ``Frequency.MIN_30``, ``Frequency.MIN_60``, ``Frequency.WEEKLY``, and
``Frequency.MONTHLY``. Pass ``frequency=`` on the method call; it does not have to match the session frequency.

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Value
     - Bar duration (data requests)
   * - ``Frequency.MIN_5``
     - Five-minute bars.
   * - ``Frequency.MIN_15``
     - Fifteen-minute bars.
   * - ``Frequency.MIN_30``
     - Thirty-minute bars.
   * - ``Frequency.MIN_60``
     - One-hour bars.
   * - ``Frequency.WEEKLY``
     - One bar per week.
   * - ``Frequency.MONTHLY``
     - One bar per month.

Example: daily backtest, 30-minute bars for an indicator:

.. code-block:: python

    session_builder.set_frequency(Frequency.DAILY)

    # Inside the strategy — session is daily, but this series is 30-minute bars
    series = self.data_provider.historical_price(
        self.ticker, PriceField.Close, nr_of_bars=20, frequency=Frequency.MIN_30
    )


*******************************************************
Tickers
*******************************************************

A ticker is a typed handle that identifies a tradable instrument. QF-Lib uses different ticker subclasses
per data provider so that the provider can interpret the identifier correctly.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Class
     - Use case
   * - ``Ticker``
     - Abstract base class. Never instantiate directly.
   * - ``BloombergTicker``
     - Bloomberg (requires ``blpapi``). Example: ``BloombergTicker("SPY US Equity")``.
   * - ``QuandlTicker``
     - Nasdaq Data Link (Quandl).
   * - ``YFinanceTicker``
     - Yahoo Finance. Example: ``YFinanceTicker("SPY")``.
   * - ``AlpacaTicker``
     - Alpaca Markets (equities and crypto). Example: ``AlpacaTicker("AAPL", SecurityType.STOCK)``.
   * - ``BinanceTicker``
     - Binance spot and derivatives.
   * - ``HaverTicker``
     - Haver Analytics macro / economic series.
   * - ``PortaraTicker``
     - Portara-exported futures data.

For **demos and unit tests**, the repository includes ``DummyTicker`` in ``demo_scripts`` (maps to synthetic CSV
data such as ``"AAA"`` … ``"FFF"``). Tutorials use it with :class:`~qf_lib.data_providers.csv.csv_data_provider.CSVDataProvider`;
production strategies should use the provider-specific ticker class that matches your data source.

.. code-block:: python

    from qf_lib.common.tickers.tickers import BloombergTicker

    ticker = BloombergTicker("SPY US Equity")
    print(ticker.as_string())


*******************************************************
Provider-specific settings examples
*******************************************************

This section shows what to put in ``settings.json`` and ``secret_settings.json`` for providers that need
settings-based configuration. For setup prerequisites and package installation commands, see
:doc:`installation`.

.. _bloomberg-blpapi-settings:

BloombergDataProvider (BLPAPI)
===============================

The provider reads host and port from ``settings.bloomberg``. See also the usage snippet in
`Other market data providers`_.

.. code-block:: json

    {
      "bloomberg": {
        "host": "localhost",
        "port": 8194
      }
    }

``secret_settings.json`` is not required for this provider unless your local setup requires additional
custom secrets outside QF-Lib defaults.

.. _quandl-settings:

QuandlDataProvider
===================

The provider reads the API key from ``settings.quandl_key``. See also the usage snippet in
`Other market data providers`_.

.. code-block:: json

    {
      "quandl_key": "YOUR_QUANDL_API_KEY"
    }

You can place this key in ``secret_settings.json`` instead:

.. code-block:: json

    {
      "quandl_key": "YOUR_QUANDL_API_KEY"
    }

.. _bloomberg-dl-settings:

BloombergDLDataProvider
========================

The provider reads Data License credentials from ``settings.bbg_dl``.

``settings.json`` example:

.. code-block:: json

    {
      "output_directory": "output",
      "bbg_dl": {
        "user": "TERMINAL_USER",
        "sn": "TERMINAL_SN"
      }
    }

``secret_settings.json`` example:

.. code-block:: json

    {
      "bbg_dl": {
        "client_id": "YOUR_CLIENT_ID",
        "client_secret": "YOUR_CLIENT_SECRET"
      }
    }

HaverDataProvider
==================

The provider reads the local Haver data path from ``settings.haver_path``.

.. code-block:: json

    {
      "haver_path": "data/haver"
    }

Usually no secret file is needed unless your environment stores credentials separately.

Providers that usually do not need settings files
==================================================

- ``CSVDataProvider`` / ``PortaraDataProvider``: configured directly via file paths in Python code.
- ``YFinanceDataProvider``: no settings keys required for standard usage.
- ``AlpacaDataProvider``: credentials are usually passed directly to constructor arguments.
- ``BinanceDataProvider``: credentials are typically handled via client configuration rather than QF-Lib settings.
- ``PresetDataProvider`` / ``PrefetchingDataProvider``: wrapper providers; they inherit configuration from source data.


*******************************************************
CSVDataProvider
*******************************************************

:class:`~qf_lib.data_providers.csv.csv_data_provider.CSVDataProvider` reads OHLCV data from a CSV
file on disk. It is perfect for offline development and unit tests.

Expected CSV format
====================
The CSV file must have a column for dates, a column for ticker names, and columns for each price field.
The demo CSV looks like this:

.. code-block:: text

    dates,tickers,open,high,low,close,volume
    2010-01-04,AAA,100.0,101.5,99.0,100.8,50000
    2010-01-04,BBB,50.0,51.2,49.8,50.5,30000
    2010-01-05,AAA,100.8,102.0,100.0,101.2,45000
    ...

Setting up CSVDataProvider
============================
.. code-block:: python

    from qf_lib.common.enums.frequency import Frequency
    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.data_providers.csv.csv_data_provider import CSVDataProvider

    from demo_scripts.common.utils.dummy_ticker import DummyTicker

    tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC')]

    field_to_price_field_dict = {
        'open':   PriceField.Open,
        'high':   PriceField.High,
        'low':    PriceField.Low,
        'close':  PriceField.Close,
        'volume': PriceField.Volume,
    }

    data_provider = CSVDataProvider(
        path="path/to/daily_data.csv",
        tickers=tickers,
        index_col='dates',
        field_to_price_field_dict=field_to_price_field_dict,
        fields=['open', 'high', 'low', 'close', 'volume'],
        ticker_col='tickers',
        # frequency defaults to Frequency.DAILY; pass Frequency.MIN_1 for intraday data
    )

    # Fetch close prices for a date range
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date

    prices = data_provider.get_price(
        tickers=DummyTicker('AAA'),
        fields=PriceField.Close,
        start_date=str_to_date('2010-01-01'),
        end_date=str_to_date('2015-12-31'),
    )
    print(prices.head())


*******************************************************
PrefetchingDataProvider
*******************************************************

For production backtests, fetching data bar-by-bar from a remote provider (Bloomberg, Quandl, etc.)
can be very slow. :class:`~qf_lib.data_providers.prefetching_data_provider.PrefetchingDataProvider`
pre-downloads the entire price range at startup and then serves every subsequent request from an
in-memory cache.

.. code-block:: python

    from qf_lib.data_providers.prefetching_data_provider import PrefetchingDataProvider
    from qf_lib.common.enums.frequency import Frequency
    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider

    tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC')]
    fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close, PriceField.Volume]
    start_date = str_to_date('2010-01-01')
    end_date = str_to_date('2020-12-31')

    # All data is downloaded once here; all subsequent get_price / historical_price calls are instant
    prefetched = PrefetchingDataProvider(
        data_provider=daily_data_provider,
        tickers=tickers,
        fields=fields,
        start_date=start_date,
        end_date=end_date,
        frequency=Frequency.DAILY,
    )

    # Pass prefetched to the session builder instead of the original data provider
    session_builder.set_data_provider(prefetched)

.. tip::
    For sessions with many tickers, the ``BacktestTradingSessionBuilder`` has a convenience method:

    .. code-block:: python

        ts.use_data_preloading(tickers)

    Call it just before ``ts.start_trading()`` to pre-fetch all fields for the listed tickers
    over the backtest date range.


*******************************************************
PresetDataProvider
*******************************************************

:class:`~qf_lib.data_providers.preset_data_provider.PresetDataProvider` wraps an in-memory
:class:`~qf_lib.containers.qf_data_array.QFDataArray` so it behaves like any other
``DataProvider``. Use it in unit tests, documentation examples, or any workflow where data is
already prepared in memory.

.. code-block:: python

    import pandas as pd
    from qf_lib.common.enums.frequency import Frequency
    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
    from qf_lib.data_providers.helpers import tickers_dict_to_data_array
    from qf_lib.data_providers.preset_data_provider import PresetDataProvider

    from demo_scripts.common.utils.dummy_ticker import DummyTicker

    ticker = DummyTicker("AAA")
    dates = pd.date_range("2010-01-01", "2010-06-01", freq="D")
    fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close, PriceField.Volume]
    prices_df = QFDataFrame(
        {f: [100.0 if f != PriceField.Volume else 1000.0 for _ in dates] for f in fields},
        index=dates,
    )
    data_array = tickers_dict_to_data_array({ticker: prices_df}, [ticker], fields)

    provider = PresetDataProvider(
        data_array, dates[0], dates[-1], Frequency.DAILY,
    )
    close = provider.get_price(ticker, PriceField.Close, dates[0], dates[-1])
    print(close)

*******************************************************
Querying data: common patterns
*******************************************************

Return types for ``get_price`` and ``historical_price`` use price-specific containers
(:class:`~qf_lib.containers.series.prices_series.PricesSeries`,
:class:`~qf_lib.containers.dataframe.prices_dataframe.PricesDataFrame`). Use ``get_history`` when you need generic
:class:`~qf_lib.containers.series.qf_series.QFSeries` / :class:`~qf_lib.containers.dataframe.qf_dataframe.QFDataFrame`
for non-OHLCV fields.

Single ticker, single field → ``PricesSeries``
================================================
.. code-block:: python

    close = data_provider.get_price(
        tickers=DummyTicker('AAA'),
        fields=PriceField.Close,
        start_date=str_to_date('2015-01-01'),
        end_date=str_to_date('2017-12-31'),
    )
    # close is a PricesSeries (DatetimeIndex, PriceField-aware)
    print(close.tail())

Multiple tickers, single field → ``PricesDataFrame``
======================================================
.. code-block:: python

    tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC')]

    prices_df = data_provider.get_price(
        tickers=tickers,
        fields=PriceField.Close,
        start_date=str_to_date('2015-01-01'),
        end_date=str_to_date('2017-12-31'),
    )
    # prices_df is a PricesDataFrame: rows = dates, columns = tickers
    print(prices_df.head())

Single ticker, multiple fields → ``PricesDataFrame``
====================================================
.. code-block:: python

    ohlcv = data_provider.get_price(
        tickers=DummyTicker('AAA'),
        fields=[PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close, PriceField.Volume],
        start_date=str_to_date('2015-01-01'),
        end_date=str_to_date('2015-03-31'),
    )
    # ohlcv is a PricesDataFrame: rows = dates, columns = PriceField values
    print(ohlcv.head())

Last N bars (inside a strategy) → ``PricesSeries``
===================================================
.. code-block:: python

    # Available as self.data_provider.historical_price(...) inside a running backtest
    last_20_closes = data_provider.historical_price(
        DummyTicker('AAA'), PriceField.Close, nr_of_bars=20
    )
    # PricesSeries of the 20 most recent closes at the current simulation time


*******************************************************
Other market data providers
*******************************************************

The snippets below use the same ``get_price`` / ``historical_price`` interface as
:class:`~qf_lib.data_providers.csv.csv_data_provider.CSVDataProvider`. Install commands refer to
the project extras in :doc:`installation` (section ``Installing optional data providers``).

.. list-table::
   :header-rows: 1
   :widths: 28 52 20

   * - Provider
     - Purpose
     - Extra install
   * - :class:`~qf_lib.data_providers.yfinance.yfinance_data_provider.YFinanceDataProvider`
     - Yahoo Finance historical data
     - ``pip install -e ".[yfinance]"``
   * - :class:`~qf_lib.data_providers.quandl.quandl_data_provider.QuandlDataProvider`
     - Nasdaq Data Link (Quandl)
     - ``pip install -e ".[quandl]"``
   * - :class:`~qf_lib.data_providers.alpaca_py.alpaca_data_provider.AlpacaDataProvider`
     - Alpaca stocks and crypto
     - ``pip install -e ".[alpaca]"``
   * - :class:`~qf_lib.data_providers.binance_dp.binance_data_provider.BinanceDataProvider`
     - Binance market data
     - ``pip install python-binance``
   * - :class:`~qf_lib.data_providers.bloomberg.bloomberg_data_provider.BloombergDataProvider`
     - Bloomberg Terminal via BLPAPI
     - ``blpapi`` (see installation)
   * - :class:`~qf_lib.data_providers.bloomberg_dl.bloomberg_dl_data_provider.BloombergDLDataProvider`
     - Bloomberg Data License datasets
     - ``pip install -e ".[bloomberg_dl]"``
   * - :class:`~qf_lib.data_providers.haver.haver_data_provider.HaverDataProvider`
     - Haver Analytics local database
     - Vendor Haver SDK (licensed)
   * - :class:`~qf_lib.data_providers.portara.portara_data_provider.PortaraDataProvider`
     - Portara-exported futures files on disk
     - none (file-based)

YFinanceDataProvider
====================

.. code-block:: python

    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.tickers.tickers import YFinanceTicker
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date
    from qf_lib.data_providers.yfinance.yfinance_data_provider import YFinanceDataProvider

    provider = YFinanceDataProvider()
    prices = provider.get_price(
        YFinanceTicker("SPY"),
        PriceField.Close,
        str_to_date("2020-01-01"),
        str_to_date("2020-12-31"),
    )


Alpaca Data Provider
=====================

.. code-block:: python

    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.enums.security_type import SecurityType
    from qf_lib.common.tickers.tickers import AlpacaTicker
    from qf_lib.data_providers.alpaca_py.alpaca_data_provider import AlpacaDataProvider

    data_provider = AlpacaDataProvider()

    # Fetch the last 10 close prices of ETH/USD (no API key needed)
    prices = data_provider.historical_price(
        AlpacaTicker("ETH/USD", SecurityType.CRYPTO),
        PriceField.Close,
        nr_of_bars=10,
    )
    print(prices)

.. note::
    :class:`~qf_lib.data_providers.alpaca_py.alpaca_data_provider.AlpacaDataProvider` provides free access
    to cryptocurrency data without requiring an API key. For equity data (e.g. AAPL) you need a free Alpaca account and API key.
    Pass ``api_key`` and ``secret_key`` to ``AlpacaDataProvider(api_key=..., secret_key=...)``.


QuandlDataProvider
==================

Requires ``quandl_key`` in settings (see :ref:`quandl-settings` above).

.. code-block:: python

    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.tickers.tickers import QuandlTicker
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date
    from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider

    from demo_scripts.demo_configuration.demo_settings import get_demo_settings

    settings = get_demo_settings()
    provider = QuandlDataProvider(settings)
    ticker = QuandlTicker("WIKI/AAPL")
    prices = provider.get_price(
        ticker, PriceField.Close,
        str_to_date("2015-01-01"), str_to_date("2015-12-31"),
    )

BloombergDataProvider
=====================

Requires ``settings.bloomberg`` (see :ref:`bloomberg-blpapi-settings` above).

.. code-block:: python

    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.tickers.tickers import BloombergTicker
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date
    from qf_lib.data_providers.bloomberg.bloomberg_data_provider import BloombergDataProvider

    from demo_scripts.demo_configuration.demo_settings import get_demo_settings

    settings = get_demo_settings()
    provider = BloombergDataProvider(settings)
    ticker = BloombergTicker("SPY US Equity")
    prices = provider.get_price(
        ticker, PriceField.Close,
        str_to_date("2015-01-01"), str_to_date("2015-12-31"),
    )

BloombergDLDataProvider
========================

Uses ``settings.bbg_dl`` (see :ref:`bloomberg-dl-settings` above). Install with
``pip install -e ".[bloomberg_dl]"``.

HaverDataProvider and PortaraDataProvider
==========================================

* **Haver** — point ``settings.haver_path`` at your local Haver database; requires a licensed Haver
  Python package from the vendor.
* **Portara** — reads Portara-exported futures files from disk; configure paths in Python like
  ``CSVDataProvider``. Use :class:`~qf_lib.common.tickers.tickers.PortaraTicker` for instrument IDs.

BinanceDataProvider
====================

.. code-block:: python

    from qf_lib.data_providers.binance_dp.binance_data_provider import BinanceDataProvider

    # Requires Binance ticker setup; credentials depend on which endpoints you use.
    provider = BinanceDataProvider()


Which provider should I use?
============================

* **Development / tests** — ``CSVDataProvider`` or ``PresetDataProvider`` for reproducible offline work.
* **Faster backtests on remote data** — wrap any provider with ``PrefetchingDataProvider`` (or
  ``BacktestTradingSession.use_data_preloading()``).
* **Quick external experiments** — ``YFinanceDataProvider`` or ``AlpacaDataProvider`` (crypto without API key).
* **Production with existing licences** — Bloomberg, Quandl, Haver, or Portara, using the settings patterns above.




