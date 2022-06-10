###########################################
Customize your backtest
###########################################

This tutorial will provide you more details related to your Backtest configuration. Afterwards you will be able to:

* include various commission models in your backtests,
* simulate various types of slippage.

All the example below use the `Simple Moving Average Strategy`_ introduced in the previous tutorial.

.. _Simple Moving Average Strategy: https://github.com/quarkfin/qf-lib/blob/master/demo_scripts/strategies/simple_ma_strategy.py

********************
Commission models
********************

After following the tutorial **How to backtest your strategy**, if you looked carefully at the Transactions file generated
by your backtest, probably you saw that the commission charged for each transaction was equal to 0. As we would like our
backtest to follow closely a real life trading example it would be a good idea to include any trading fees and commissions
into the computation.

To add a commission model to the Backtest Trading Session, we use the `set_commission_model` function on the `BactestTradingSessionBuilder`.
This function accepts the type of the Commission Model as the first parameter and all models parameters as keyword arguments.

Fixed commissions
-----------------
Let's start with a simple example, where we add a fixed commission of 2.75 to every transactions (the commission is
expressed in the currency of the traded asset, e.g. 1.0 could denote 1.0 USD).


.. code-block::
    :caption: Add fixed commission to your daily backtest

    from qf_lib.backtesting.execution_handler.commission_models.fixed_commission_model import \
        FixedCommissionModel

    def main():
        ticker = DummyTicker("AAA")
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")

        session_builder = container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_data_provider(daily_data_provider)

        session_builder.set_commission_model(FixedCommissionModel, commission=2.75)

        ts = session_builder.build(start_date, end_date)

Now let's run the backtest and compare it to the previous backtest, which did not include commissions.
After the backtest finishes, as the first step we can view the Transactions file to make sure that the commission was included.

We can also compare the Total Return of the strategy (either from the console output or from the table in the Tearsheet document).
The difference in this case is negligibly small, as we had less than 80 transactions in total within the 4 years of the backtest and the
default initial value of the portfolio equals 10,000,000, however in case of more frequent trading the commissions may add up and therefore it
is useful to include them in your backtest.

Basis points commissions
------------------------------

In case if you would like to use a fixed bps rate for your trades value, you could use the `BpsTradeValueCommissionModel`.
For example the configuration below will always use 2pbs of the value of the trade as the commission.

.. code-block::
    :caption: Add fixed bps commission to your daily backtest

    from qf_lib.backtesting.execution_handler.commission_models.bps_trade_value_commission_model import \
        BpsTradeValueCommissionModel

    def main():
        # settings
        backtest_name = 'Simple MA Strategy Demo'
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")
        ticker = DummyTicker("AAA")

        # configuration
        session_builder = container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_backtest_name(backtest_name)
        session_builder.set_data_provider(daily_data_provider)

        session_builder.set_commission_model(BpsTradeValueCommissionModel, commission=2.0)

        ts = session_builder.build(start_date, end_date)

        strategy = SimpleMAStrategy(ts, ticker)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

Interactive Brokers commission model
-------------------------------------
Another commission model, which you can use in your backtests, is the Interactive Brokers commission model based on the US Fixed pricing.
If you would like to see the pricing details, they are available `here`_.

.. _here: https://www.interactivebrokers.co.uk/en/index.php?f=1590&p=stocks1

.. code-block::
    :caption: Add Interactive Brokers commission to your daily backtest

    from qf_lib.backtesting.execution_handler.commission_models.ib_commission_model import \
        IBCommissionModel

    def main():
        # settings
        backtest_name = 'Simple MA Strategy Demo'
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")
        ticker = DummyTicker("AAA")

        # configuration
        session_builder = container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_backtest_name(backtest_name)
        session_builder.set_data_provider(daily_data_provider)

        session_builder.set_commission_model(IBCommissionModel)

        ts = session_builder.build(start_date, end_date)

        strategy = SimpleMAStrategy(ts, ticker)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

********************
Slippage models
********************

Why should I use slippage in my backtests?
------------------------------------------

In the examples before we assumed that there is no difference between the expected price of a transaction and the price
at which we executed it. However, in real life this is often not the case. Therefore, to simulate less ideal market conditions,
the next examples will introduce slippage into our backtests. By running the examples you will be able to see that
the impact of the slippage on your strategy may have a significant impact on the performance.

Fixed Slippage
------------------

Let's start with a simple example with `FixedSlippage` model. This model always adds (or subtracts if short sale)
certain absolute amount of money to the price. For example, to always add a 0.25$ slippage to our backtest, we should
change our script to include the following:

.. code-block::
    :caption: Add 0.25$ slippage

    from qf_lib.backtesting.execution_handler.slippage.fixed_slippage import \
        FixedSlippage

    def main():
        # settings
        backtest_name = 'Simple MA Strategy Demo'
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")
        ticker = DummyTicker("AAA")

        # configuration
        session_builder = container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_backtest_name(backtest_name)
        session_builder.set_data_provider(daily_data_provider)

        session_builder.set_slippage_model(FixedSlippage, slippage_per_share=0.25)

        ts = session_builder.build(start_date, end_date)

        strategy = SimpleMAStrategy(ts, ticker)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

If you will run the Simple Moving Average Strategy with the Fixed Slippage, you can see in the Transactions file, that
the fill prices of the transactions are now bigger by 0.25$ than the fill prices in case if no slippage was added.

Also, as you probably already noticed, the performance of the strategy decreased significantly. This shows us that our
Simple Moving Average strategy would not perform that well in non ideal market conditions, where the fill price is not equal
to the Open or Close daily price of the asset.

Price Based Slippage
---------------------

The fixed slippage model may be useful in case if we know an estimated slippage value to add or subtract from our
fills prices. However, if we run a long backtest on a certain asset, its prices range may be very wide and it would be
hard to choose a fixed slippage value.

For example in case if the price of the asset was ~15$ in the first year of the backtest and ~400$ in the last year of the
backtest, the slippage will have a different impact on the transaction in each of these years.

To avoid this, we can use another slippage model - `PriceBasedSlippage`, which calculates the slippage by using some
fixed fraction of the current securities' price (e.g. always 0.1%).


.. code-block::
    :caption: Add 0.1% slippage

    from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import \
        PriceBasedSlippage

    def main():
        # settings
        backtest_name = 'Simple MA Strategy Demo'
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")
        ticker = DummyTicker("AAA")

        # configuration
        session_builder = container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_backtest_name(backtest_name)
        session_builder.set_data_provider(daily_data_provider)

        session_builder.set_slippage_model(PriceBasedSlippage, slippage_rate=0.001)

        ts = session_builder.build(start_date, end_date)

        strategy = SimpleMAStrategy(ts, ticker)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

Square Root Market Impact Slippage
-----------------------------------
A more sophisticated slippage model is the Square Root Market Impact Slippage. In this case slippage is based on the
square-root formula for market impact modelling. The price slippage is calculated by multiplying
no-slippage-price by (1 + market impact), where the market impact is defined as the product of volatility,
square of the volume and volatility ratio(volume traded in bar / average daily volume) and a constant value (price_impact).

The direction of the slippage is always making the price worse for the trader (it increases the price when
buying and decreases when selling).

.. code-block::
    :caption: Add square root market impact slippage

    from qf_lib.backtesting.execution_handler.slippage.square_root_market_impact_slippage import \
        SquareRootMarketImpactSlippage

    def main():
        # settings
        backtest_name = 'Simple MA Strategy Demo'
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")
        ticker = DummyTicker("AAA")

        # configuration
        session_builder = container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_backtest_name(backtest_name)
        session_builder.set_data_provider(daily_data_provider)

        session_builder.set_slippage_model(SquareRootMarketImpactSlippage, price_impact=0.05)

        ts = session_builder.build(start_date, end_date)

        strategy = SimpleMAStrategy(ts, ticker)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()


Limit fills volume
--------------------
In all the previous examples we ignored the volume parameter of the asset. However, this may result in us creating an order
with volume exceeding the real life volume. Maybe you already thought about this and you tried to adjust the desired order volume based on
the historical volume of the asset (for example if the daily volume never exceeded 1000 than creating an order of size 10,000 does not simply make sense).
Indeed, that is a good idea! But what if the volume was high for the past days or months and exactly
on the day, when you wanted to send the order it suddenly dropped? The above mentioned approach will not help us in this case. What you
can do to address this issue is to use the `max_volume_share_limit` parameter of the Slippage.

Slippage models can not only change the fill price of the transaction, but they can also limit the Order's volume depending on the volume for a particular
day. The `max_volume_share_limit` parameter should be a float number from range [0,1] and it would denote how big (volume-wise) the Order can be.
I.e. if it's 0.5 and the daily volume for a given asset is 1,000,000 USD, then the max volume of the fill will not exceed be 500,000 USD.

Let's see how the Simple Moving Average strategy would perform in case of 0.1% price slippage and 15% max volume share limit:

.. code-block::
    :caption: Add square root market impact slippage

    from qf_lib.backtesting.execution_handler.slippage.price_based_slippage import \
        PriceBasedSlippage

    def main():
        # settings
        backtest_name = 'Simple MA Strategy Demo'
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")
        ticker = DummyTicker("AAA")

        # configuration
        session_builder = container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_backtest_name(backtest_name)
        session_builder.set_data_provider(daily_data_provider)

        session_builder.set_slippage_model(PriceBasedSlippage, slippage_rate=0.001,
            max_volume_share_limit=0.15)

        ts = session_builder.build(start_date, end_date)

        strategy = SimpleMAStrategy(ts, ticker)

        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

Let's run the backtest and compare the results with the initial strategy performance!

After the test finished we can see that actually our strategy was not as good as it seemed to be after the initial runs. The price slippage
of 0.01% and allowing only up to 15% of the daily volume in the fills completely changed the performance of our strategy.

.. code-block::

                             Simple MA Strategy Demo
    Start Date                         2010-01-02
    End Date                           2015-03-01
    Total Return                            -4.12 %
    Annualised Return                       -0.81 %
    Annualised Volatility                    4.24 %
    Annualised Upside Vol.                   3.75 %
    Annualised Downside Vol.                 3.86 %
    Sharpe Ratio                            -0.19
    Omega Ratio                              0.97
    Calmar Ratio                            -0.06
    Gain to Pain Ratio                      -0.10
    Sorino Ratio                            -0.21
    5% CVaR                                 -0.69 %
    Annualised 5% CVaR                     -10.44 %
    Max Drawdown                            12.99 %
    Avg Drawdown                             3.08 %
    Avg Drawdown Duration                   72.56 days
    Best Return                              1.46 %
    Worst Return                            -1.65 %
    Avg Positive Return                      0.21 %
    Avg Negative Return                     -0.21 %
    Skewness                                -0.09
    No. of daily samples                     1885