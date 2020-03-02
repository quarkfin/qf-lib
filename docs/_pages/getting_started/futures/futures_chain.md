---
permalink: /futures/futures_chain
title: "FuturesChain"
classes: wide
---

# `class FuturesChain(future_ticker, data_provider)`

The `FuturesChain` class facilitates the futures contracts management. Its main functionality is provided by the `get_price` function, which returns a PricesDataFrame (PricesSeries) of prices for the given `FutureTicker`, automatically managing the contracts chaining.

## Parameters

| **future_ticker:** ***FutureTicker*** | The `FutureTicker` used to download the futures contracts, further chained and joined in order to obtain the result of `get_price` function. |
| **data_provider**: ***DataProvider*** | Reference to the data provider, necessary to download latest prices, returned by the `get_price` function. |

## Methods
### `def get_price(self, fields, start_date, end_date, frequency=Frequency.DAILY, method=FuturesAdjustmentMethod.NTH_NEAREST)`

Combines consecutive specific `FutureContracts` data, in order to obtain a chain of prices.

#### Parameters

| **fields:** ***PriceField, Sequence[PriceField]*** | Data fields, corresponding to Open, High, Low, Close prices and Volume, that should be returned by the function. |
| **start_date:** ***datetime*** | First date for which the chain needs to be created. |
| **end_date:** ***datetime*** | Last date for which the chain needs to be created. |
| **frequency:** ***optional, default daily*** | Frequency of the returned data, by default set to daily frequency. |
| **method:** ***optional, default N-th nearest*** | `FuturesAdjustmentMethod` corresponding to one of two available methods of chaining the futures contracts. In case of the default `NTH_NEAREST` method, the price data for a certain period of time is simply taken from the N-th contract, and there is no discontinuities correction at the contract expiry dates. In case of the `BACK_ADJUST` method, the historical price discontinuities are corrected, so that they would align smoothly on the expiry date. The gaps between consecutive contracts are being adjusted, by shifting the historical data by the difference between the Open price on the first day of new contract and Close price on the last day of the old contract (where first / last days of contracts are defined by the days_before_exp_date in the `FutureTicker`). The back adjustment considers only the Open, High, Low, Close price values. The Volumes are not being adjusted. |

#### Returns

| **PricesDataFrame or PricesSeries** | The resulting prices. |

#### Example


```
>>> MarketOpenEvent.set_trigger_time({"hour": 13, "minute": 30, "second": 0, "microsecond": 0})
>>> MarketCloseEvent.set_trigger_time({"hour": 20, "minute": 0, "second": 0, "microsecond": 0})

>>> settings = get_test_settings()
>>> bbg_provider = BloombergDataProvider(settings)
>>> bbg_provider.connect()

>>> timer = SettableTimer()
>>> timer.set_current_time(str_to_date("2018-05-01"))

>>> ticker = BloombergFutureTicker("C {} Comdty", 1, 10, 1, name="Corn")
>>> ticker.initialize_data_provider(timer, bbg_provider)

>>> futures_chain = FuturesChain(ticker, data_provider)
>>> futures_chain.get_price([PriceField.Close, PriceField.Open], str_to_date("2018-04-20"), str_to_date("2018-04-24"))
fields      PriceField.Close  PriceField.Open
dates
2018-04-20    33.50    32.75
2018-04-21    32.50    32.00
2018-04-22    31.75    31.75
2018-04-23    33.25    33.25
2018-04-24    33.00    33.50
dtype: float64
```
