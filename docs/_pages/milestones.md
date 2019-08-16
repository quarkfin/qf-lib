---
permalink: /milestones/
title: "Milestones"
---

The development goals are linked to the two main limitations of the backtester:

### Frequency of the data
At the moment, the library operates in the ‘end of day’ regime. It means that any trading and strategy testing can be done using daily data or data of lower frequency (such as monthly or weekly) but intraday tests are not available.
We are working on implementing intraday backtesting and trading functionalities.

### Supported asset classes
The library supports Equities, Indices, FX and Equity like products which have a continuous timeseries of prices or returns. The backtesting of investment products based on the term structure (like Futures, or Fixed Income) is not supported.
Adding a possibility of chaining the contracts and therefore run long backtest on these instruments is an another development goal.
