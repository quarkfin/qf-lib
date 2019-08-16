---
permalink: /docs/features/
title: "Features"
---

The most important features of the Library are as follows:

## Flexible data sourcing
The project supports the possibility of an easy selection of the data source. It currently provides financial data from Bloomberg, Quandl, Haver Analytics, CoinMarketCap or from an traditional database (Oracle, PostgreSQL) however, the DataProvider interface can be extended to support any other source of data. In the case of complex computations, the operation time can be reduced by using data preloading. The data structures can be also cached to avoid sending excess requests if the tests are expected to be carried out multiple times. In addition, if the data is partially incomplete (i.e. has gaps); it can be easily cleaned – for example using regression.

## Tools to prevent look-ahead bias in the backtesting environment
All DataProvider types (including custom) can be wrapped with a DataHandler, which may be used in both live and backtest environments. Its task is to make sure that data "from the future" will not be passed into the testing components. It is particularly essential in the Backtester.

##	Adapted data containers
In order to facilitate the processing of financial data, QF-Lib introduces custom time-indexed data structures, which allow storing and performing calculations on prices, price returns or logarithmic price returns much more easily. The introduced structures are 1, 2, and 3-dimensional, and they facilitate the conversion from one data type to another. Any time-indexed pandas `DataFrame` or `Series` can be cast to a specific type using the `cast_dataframe` and `cast_series` functions.

## Summary generation
All performed studies can be summarized with a practical and informative document explaining the results. Several document templates are available in the project, but the convenient interfaces allow creating custom ones. They can contain the generated charts, tables with financial statistics or any other elements. Supported file types include PDF, Microsoft Excel or HTML. The documents can be then automatically published to desired e-mail addresses.

## Simple adjustment of existing settings and creation of new functionalities
The project has been developed with the intention of being flexible and customizable. Its architecture supports all-purpose use, allowing for performing miscellaneous tests and studies. The QF-Lib library can be understood as a financial ‘multi-tool’ for every code developer, who wishes to facilitate his or her research.
