---
permalink: /futures/future_ticker
title: "FutureTicker"
classes: wide
---
# `class FutureTicker(family_id, N, days_before_exp_date, point_value=1.0, name="")`

The `FutureTicker` class extends the standard `Ticker` class. It allows the user to use only a Ticker abstraction, which provides all of the standard Ticker functionalities (e.g.
just as standard tickers, it can be used along with `DataHandler` functions `get_price`, `get_last_available_price`, `get_current_price` etc.), without the need to manually manage
the rolling of the contracts or to select a certain specific Ticker.

## Parameters

| **name:** ***str*** | Field which contains name (or a short description_ of the FutureTicker. |
| **family_id:** ***str*** | Identificator used to describe the whole family of future contracts. In case of specific Future Tickers (like e.g. `BloombergFutureTicker`) its purpose is to build an identificator, used by the data provider to download the chain of corresponding Tickers, and to verify whether a specific Ticker belongs to a certain futures family. |
| **N:** ***int*** | Used to identify which specific Ticker should be considered by the Backtester, while using the general Future Ticker class. For example N parameter set to 1, denotes the front future contract. |
| **days_before_exp_date:** ***int*** | Number of days before the expiration day of each of the contract, when the "current" specific contract should be substituted with the next consecutive one. |
| **point_value:** ***float, optional, default 1.0*** | Used to define the size of the contract. |

## Attributes

| **ticker** | Property which returns the value of 'ticker' attribute of the currently valid, specific `Ticker`, e.g. in case of Cotton `FutureTicker` in the beginning of December, before the expiration date of the December ticker, the function will return the `Ticker("CTZ9 Comdty").ticker` string value. |

## Methods

| **belongs_to_family**(self, ticker: `Ticker`) | Function, which takes a specific Ticker, and verifies if it belongs to the family of futures contracts, identified by the `FutureTicker`. |
| **get_current_specific_ticker**(self) | Method which returns the currently valid, specific Ticker. It the ticker of *N*-th Future Contract for the provided date, assuming that *days_before_exp_date* days before the original expiration the ticker of the next contract will be returned. E.g. if days_before_exp_date = 4 and the expiry date = 16th July, then the old contract will be returned up to 16 - 4 = 12th July (inclusive). The function may raise `NoValidTickerException` if no specific Ticker exists for the given point of time, which is defined by the `Timer` (therefore there is no need to provide any additional dates). |
| **get_expiration_dates**(self) | Returns the QFSeries containing the list of specific future contracts Tickers, indexed by their expiration dates. The index contains original expiration dates, as returned by the data handler, without shifting it by the days_before_exp_date days. |
| **initialize_data_provider**(self, timer: Timer, data_provider: DataProvider) | Initializes the `FutureTicker` by setting the `Timer` and `DataProvider`, used further to load the future chain tickers. |
