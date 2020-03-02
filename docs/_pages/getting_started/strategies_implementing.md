---
permalink: /strategies_implementing/
title: "Strategies implementing"
toc: true
toc_sticky: true
toc_label: "On this page"
toc_icon: "cog"
---

This document will guide you through the process of implementing and backtesting your own strategies.

To run a backtest:
- create a `TradingSession` (for `BacktestTradingSession` use `BacktestTradingSessionBuilder`),
- build a dictionary of `AlphaModel` and `Ticker` assigned to them,
- (optionally) preload price data and add use them in the `TradingSession`,
- create a trading **Strategy**,
- call `start_trading()` method on the `TradingSession`.

All the below described strategies can be found in `qf-lib/demo_scripts`.

# Basic strategy implementations

In order to be used for the backtesting purposes, strategies do not have to implement any given interfaces. As they need to react to certain (also user defined) events, the only requirement imposed is that the strategies subscribe to a set of events and implement the corresponding callback methods.

## Simple Moving Average strategy implementation

In this section we will present an example of a strategy, which computes every day, before the market open time, two simple moving averages (long - 20 days, short - 5 days) and creates a buy order in case if the short moving average is greater or equal to the long moving average.

The crucial part of strategy implementation is subscribing to events and implementing the corresponding callback methods. In our case we will calculate the signals and place orders before opening the market (we subscribe to the `BeforeMarketOpenEvent`, the default time of it as defined in the `BacktestTradingSessionBuilder` is 8:00 a.m.). Then, all the placed orders can be executed already on the market opening.

```
class SimpleMAStrategy(object):
    def __init__(self, ts: BacktestTradingSession, ticker: Ticker):
        self.broker = ts.broker
        self.order_factory = ts.order_factory
        self.data_handler = ts.data_handler
        self.contract_ticker_mapper = ts.contract_ticker_mapper
        self.position_sizer = ts.position_sizer
        self.timer = ts.timer
        self.ticker = ticker

        # Subscribe to the BeforeMarketOpenEvent
        ts.notifiers.scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        # Compute the moving averages
        long_ma_len = 20
        short_ma_len = 5

        # Use data handler to download last 20 daily close prices and use them
        # to compute the moving averages
        long_ma_series = self.data_handler.historical_price(self.ticker,
          PriceField.Close, long_ma_len)
        long_ma_price = long_ma_series.mean()

        short_ma_series = long_ma_series.tail(short_ma_len)
        short_ma_price = short_ma_series.mean()

        # Map the given ticker onto a Contract object, which can be further used
        # to place an Order
        contract = self.contract_ticker_mapper.ticker_to_contract(self.ticker)

        if short_ma_price >= long_ma_price:
            # Place a buy Market Order, adjusting the position to a value equal
            # to 100% of the portfolio
            orders = self.order_factory.target_percent_orders({contract: 1.0},
              MarketOrder(), TimeInForce.DAY)
        else:
            orders = self.order_factory.target_percent_orders({contract: 0.0},
              MarketOrder(), TimeInForce.DAY)

        # Cancel any open orders and place the newly created ones
        self.broker.cancel_all_open_orders()
        self.broker.place_orders(orders)


def main():
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2010-03-01")
    ticker = BloombergTicker("MSFT US Equity")

    # Build the BacktestTradingSession
    session_builder = container.resolve(BacktestTradingSessionBuilder)
    # Use daily price bars
    session_builder.set_frequency(Frequency.DAILY)
    session_builder.set_backtest_name('Simple_MA')
    ts = session_builder.build(start_date, end_date)
    ts.use_data_preloading(ticker, RelativeDelta(days=40))

    SimpleMAStrategy(ts, ticker)
    ts.start_trading()
```

## Buy and Hold strategy implementation

In this section we will present an example of a strategy, which simply purchases (longs) an asset as soon as it starts and then holds until the completion of a backtest.

```

class BuyAndHoldStrategy(object):
    CONTRACT = Contract(symbol="SPY US Equity", security_type='STK',
     exchange='NASDAQ')
    TICKER = BloombergTicker("SPY US Equity")

    def __init__(self, broker: Broker, order_factory: OrderFactory,
      scheduler: Scheduler):
        self.order_factory = order_factory
        self.broker = broker

        self.invested = False

        # Subscribe to the BeforeMarketOpenEvent
        scheduler.subscribe(BeforeMarketOpenEvent, listener=self)

    def on_before_market_open(self, _: BeforeMarketOpenEvent):
        self.calculate_signals()

    def calculate_signals(self):
        if not self.invested:
            orders = self.order_factory.percent_orders({self.CONTRACT: 1.0},
              MarketOrder(), TimeInForce.GTC)

            self.broker.place_orders(orders)
            self.invested = True


def main():
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2018-01-01")

    session_builder = container.resolve(BacktestTradingSessionBuilder)  
    session_builder.set_backtest_name('Buy and Hold')
    session_builder.set_frequency(Frequency.DAILY)
    ts = session_builder.build(start_date, end_date)
    ts.use_data_preloading(BuyAndHoldStrategy.TICKER)

    BuyAndHoldStrategy(
        ts.broker,
        ts.order_factory,
        ts.notifiers.scheduler
    )

    ts.start_trading()
```

# AlphaModel strategy implementation
A different approach to strategies implementation involves the use of AlphaModels. The **backtesting** module contains both an abstract `AlphaModel` and an `AlphaModelStrategy` - a base strategy, which puts together models and all settings around it and generates orders on the Before Market Open event.

`AlphaModel` is responsible for calculating Signals every day, before the market opening. Each Signal contains information such as suggested exposure, fraction at risk (helpful to determine the stop loss levels), signal confidence or expected price move. These signals are further used by the `PositionSizer` in order to generate and place `Orders`.

In order to use the `AlphaModelStrategy` it is necessary to implement the `AlphaModel.calculate_exposure()` function, which returns the expected Exposure, the key part of a generated Signal. Exposure suggests the trend direction for managing the trading position (LONG, OUT or SHORT).

Below we present a simple strategy using the `AlphaModel`. It applies two Exponential Moving Averages of different time periods on the recent market close prices of an asset to determine the suggested move. It suggests to go LONG on this asset if the shorter close prices moving average exceeds the longer one. Otherwise it suggests to go SHORT.

```
class MovingAverageAlphaModel(AlphaModel):
    settings = AlphaModelSettings(
        parameters=(5, 20),
        risk_estimation_factor=1.25
    )

    def __init__(self, fast_time_period: int, slow_time_period: int,
                 risk_estimation_factor: float, data_handler: DataHandler):
        super().__init__(risk_estimation_factor, data_handler)

        self.fast_time_period = fast_time_period
        self.slow_time_period = slow_time_period

        if fast_time_period < 3:
            raise ValueError('timeperiods shorter than 3 are pointless')
        if slow_time_period <= fast_time_period:
            raise ValueError('slow MA time period should be longer than fast
            MA time period')

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure)
      -> Exposure:
        num_of_bars_needed = self.slow_time_period
        close_tms = self.data_handler.historical_price(ticker, PriceField.Close,
          num_of_bars_needed)

        fast_ma = talib.MA(close_tms, self.fast_time_period, matype=1)  
        slow_ma = talib.MA(close_tms, self.slow_time_period, matype=1) 

        if fast_ma[-1] > slow_ma[-1]:
            return Exposure.LONG
        else:
            return Exposure.SHORT
```
