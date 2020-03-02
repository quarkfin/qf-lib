---
permalink: /futures/
title: "Futures Contracts"
toc: true
toc_sticky: true
toc_label: "On this page"
toc_icon: "cog"
---

This document describes the main components of the system, which are used in order to enable the chaining of futures contracts and running long backtests on these instruments.

# Main components

In order to support futures contracts, the following classes were introduced:
* FutureTicker,
* FutureContract,
* FuturesChain.

## `FutureTicker`

The `FutureTicker` class extends the standard `Ticker` class. It allows the user to use only a Ticker abstraction, which provides all of the standard Ticker functionalities (e.g.
just as standard tickers, it can be used along with `DataHandler` functions `get_price`, `get_last_available_price`, `get_current_price` etc.), without the need to manually manage
the rolling of the contracts or to select a certain specific Ticker.

**Important note:** While downloading historical data (using for example `get_price` function) all of the prices would be provided for the **current specific ticker**, e.g. in case
of the family of Cotton future contracts, if on a certain day the specific contract returned by the `FutureTicker` will be the
December 2019 Cotton contract, all of the prices returned by `get_price` will pertain to this specific December contract and no prices chaining will occur. In order to use the `get_price`
function along with futures contracts chaining (and eventual adjustments), the `FuturesChain` object has to be used.
{: .notice--danger}

[FutureTicker API Reference]({{ "/futures/future_ticker" | prepend:site.baseurl}})

## `FutureContract`

The `FutureContract` is a simple class representing one futures contract. The `FutureContract` objects are used by the `FuturesChain`, in order to provide the contracts chaining possibilities.
It requires 3 parameters: `ticker`, which is the symbol of the specific future contract (e.g. BloombergFutureTicker("CTZ9 Comdty")), expiration date of the contract and a `PricesDataFrame`, containing dates with price field values.

## `FuturesChain`

The `FuturesChain` class facilitates the futures contracts management. It allows to use `get_price` function, which returns a PricesDataFrame (PricesSeries), automatically managing the contracts chaining.

[FuturesChain API Reference]({{ "/futures/futures_chain" | prepend:site.baseurl}})
