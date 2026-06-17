########################################
Portfolio Construction
########################################

The ``qf_lib.portfolio_construction`` module provides a set of optimisation-based portfolio models that compute
asset weights from historical return data. This tutorial covers the most common use cases:

* Building a covariance matrix from a price series.
* Computing weights with :class:`~qf_lib.portfolio_construction.portfolio_models.min_variance_portfolio.MinVariancePortfolio`.
* Computing weights with :class:`~qf_lib.portfolio_construction.portfolio_models.max_sharpe_ratio_portfolio.MaxSharpeRatioPortfolio`.
* Inverse-volatility weighting with :class:`~qf_lib.portfolio_construction.portfolio_models.risk_parity_portfolio.RiskParityPortfolio`.
* Equal risk contribution with :class:`~qf_lib.portfolio_construction.portfolio_models.equal_risk_contribution_portfolio.EqualRiskContributionPortfolio`.
* Incorporating analyst views with :class:`~qf_lib.portfolio_construction.black_litterman.black_litterman.BlackLitterman`.
* Feeding optimised weights into a backtest.

.. note::
    Portfolio optimisation requires additional optimisation dependencies.
    Install them with:

    .. code:: console

       $ pip install -e ".[detailed_analysis]"

    At minimum, ensure ``cvxopt`` is installed before running the examples below.



*******************************************************
Preparing input data
*******************************************************

All portfolio models consume a :class:`~qf_lib.containers.dataframe.qf_dataframe.QFDataFrame` of **price** or
**return** data. The example below retrieves daily close prices for four demo tickers and computes the
covariance matrix of their simple returns, which is the most common input.

.. code-block:: python

    from qf_lib.common.enums.price_field import PriceField
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider

    start_date = str_to_date('2010-01-01')
    end_date = str_to_date('2015-12-31')

    tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC'), DummyTicker('DDD')]

    # Fetch daily close prices for all tickers as a QFDataFrame
    prices_df = daily_data_provider.get_price(
        tickers=tickers,
        fields=PriceField.Close,
        start_date=start_date,
        end_date=end_date,
    )
    prices_df.ffill(inplace=True)  # fill any gaps

    # Compute simple returns and then the covariance matrix
    returns_df = prices_df.to_simple_returns()
    cov_matrix = returns_df.cov()  # pandas .cov() returns a QFDataFrame when called on a QFDataFrame
    mean_returns = returns_df.mean()

    print("Asset names:", list(cov_matrix.columns))
    print("Covariance matrix:\n", cov_matrix)

.. tip::
    For a more robust covariance estimate (especially with many assets and short history), see the
    :ref:`robust-covariance` section below.


*******************************************************
Minimum Variance Portfolio
*******************************************************

The :class:`~qf_lib.portfolio_construction.portfolio_models.min_variance_portfolio.MinVariancePortfolio`
finds the portfolio on the efficient frontier with the smallest possible volatility. It only requires the
covariance matrix - expected returns are not needed.

.. code-block:: python

    from qf_lib.portfolio_construction.portfolio_models.min_variance_portfolio import MinVariancePortfolio

    portfolio = MinVariancePortfolio(cov_matrix=cov_matrix)
    weights = portfolio.get_weights()

    print("Min-Variance weights:")
    for ticker, w in weights.items():
        print(f"  {ticker}: {w:.2%}")

You can cap each asset's allocation with ``upper_constraint``:

.. code-block:: python

    # No single asset can exceed 40% of the portfolio
    portfolio = MinVariancePortfolio(cov_matrix=cov_matrix, upper_constraint=0.40)
    weights = portfolio.get_weights()

You can also pass a per-asset list of upper bounds:

.. code-block:: python

    # Per-asset caps: 50%, 30%, 30%, 40%
    caps = [0.50, 0.30, 0.30, 0.40]
    portfolio = MinVariancePortfolio(cov_matrix=cov_matrix, upper_constraint=caps)
    weights = portfolio.get_weights()


*******************************************************
Maximum Sharpe Ratio Portfolio
*******************************************************

:class:`~qf_lib.portfolio_construction.portfolio_models.max_sharpe_ratio_portfolio.MaxSharpeRatioPortfolio`
maximises the Sharpe ratio, which requires both the covariance matrix **and** the expected (mean) returns.

.. code-block:: python

    from qf_lib.portfolio_construction.portfolio_models.max_sharpe_ratio_portfolio import MaxSharpeRatioPortfolio

    portfolio = MaxSharpeRatioPortfolio(
        cov_matrix=cov_matrix,
        mean_returns=mean_returns,
        risk_free_rate=0.0,       # annualised risk-free rate; 0.0 is typical for backtesting
        upper_constraint=0.50,    # optional per-asset cap
    )
    weights = portfolio.get_weights()

    print("Max-Sharpe weights:")
    for ticker, w in weights.items():
        print(f"  {ticker}: {w:.2%}")


*******************************************************
Risk Parity Portfolio
*******************************************************

The :class:`~qf_lib.portfolio_construction.portfolio_models.risk_parity_portfolio.RiskParityPortfolio`
allocates inversely proportional to each asset's historical volatility - lower-volatility assets receive
more weight, so each asset contributes equally to overall portfolio risk in a first-order approximation.

Unlike the mean-variance models above, it takes the **price** (or return) DataFrame directly, not a
pre-computed covariance matrix:

.. code-block:: python

    from qf_lib.portfolio_construction.portfolio_models.risk_parity_portfolio import RiskParityPortfolio

    portfolio = RiskParityPortfolio(input_dataframe=prices_df)
    weights = portfolio.get_weights()

    print("Risk Parity weights:")
    for ticker, w in weights.items():
        print(f"  {ticker}: {w:.2%}")


*******************************************************
Equal Risk Contribution Portfolio
*******************************************************

:class:`~qf_lib.portfolio_construction.portfolio_models.equal_risk_contribution_portfolio.EqualRiskContributionPortfolio`
is a more rigorous version of risk parity: it numerically solves for weights such that each asset's
*marginal risk contribution* (based on the full covariance matrix) is identical.

.. code-block:: python

    from qf_lib.portfolio_construction.portfolio_models.equal_risk_contribution_portfolio import \
        EqualRiskContributionPortfolio

    portfolio = EqualRiskContributionPortfolio(cov_matrix=cov_matrix)
    weights = portfolio.get_weights()

    print("ERC weights:")
    for ticker, w in weights.items():
        print(f"  {ticker}: {w:.2%}")


*******************************************************
Simulating a portfolio return stream
*******************************************************

Once you have weights you can simulate the strategy's historical returns using the static helpers on the
base :class:`~qf_lib.portfolio_construction.portfolio_models.portfolio.Portfolio` class.

Constant weights (with daily rebalancing)
==========================================
.. code-block:: python

    from qf_lib.portfolio_construction.portfolio_models.portfolio import Portfolio

    portfolio_returns, allocation_df = Portfolio.constant_weights(
        assets_rets_df=returns_df,
        weights=weights,
    )

    print("Annualised return:", portfolio_returns.mean() * 252)
    print("Annualised vol:   ", portfolio_returns.std() * (252 ** 0.5))

Drifting weights (no rebalancing)
====================================
If you do not rebalance, the weights drift as prices move. Use:

.. code-block:: python

    portfolio_returns, allocation_df = Portfolio.drifting_weights(
        assets_rets_df=returns_df,
        weights=weights,
    )

The ``allocation_df`` DataFrame has one column per ticker and one row per date, showing the actual
allocation at each point in time.

Equal-weight baseline
======================
A useful sanity-check is the 1/N equal-weight portfolio:

.. code-block:: python

    eq_weights = Portfolio.one_over_n_weights(tickers)
    eq_returns, _ = Portfolio.constant_weights(returns_df, eq_weights)
    print("Equal-weight mean daily return:", eq_returns.mean())


.. _robust-covariance:

*******************************************************
Robust covariance estimation
*******************************************************

The sample covariance matrix is noisy when the number of observations is not much larger than the number
of assets. :class:`~qf_lib.portfolio_construction.covariance_estimation.robust_covariance.RobustCovariance`
applies a shrinkage estimator (Ledoit-Wolf style) that reduces estimation error:

.. code-block:: python

    from qf_lib.portfolio_construction.covariance_estimation.robust_covariance import RobustCovariance

    robust_cov = RobustCovariance(returns_df)
    shrunken_cov_matrix = robust_cov.get_covariance()

    # Drop-in replacement: use shrunken_cov_matrix wherever cov_matrix was used
    portfolio = MinVariancePortfolio(cov_matrix=shrunken_cov_matrix)
    weights = portfolio.get_weights()



*******************************************************
Using weights in a backtest
*******************************************************

Optimised weights integrate naturally with ``target_percent_orders`` inside any strategy:

.. code-block:: python

    import matplotlib.pyplot as plt

    from qf_lib.backtesting.events.time_event.regular_time_event.calculate_and_place_orders_event import \
        CalculateAndPlaceOrdersRegularEvent

    plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

    from demo_scripts.common.utils.dummy_ticker import DummyTicker
    from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
    from demo_scripts.demo_configuration.demo_settings import get_demo_settings
    from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
    from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
    from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
    from qf_lib.common.enums.frequency import Frequency
    from qf_lib.common.utils.dateutils.string_to_date import str_to_date


    from qf_lib.backtesting.strategies.abstract_strategy import AbstractStrategy
    from qf_lib.backtesting.order.execution_style import MarketOrder
    from qf_lib.backtesting.order.time_in_force import TimeInForce
    from qf_lib.portfolio_construction.portfolio_models.min_variance_portfolio import MinVariancePortfolio
    from qf_lib.common.enums.price_field import PriceField

    class MinVarianceStrategy(AbstractStrategy):
        """
        Recomputes a Min-Variance portfolio every day and rebalances accordingly.
        """

        def __init__(self, ts, tickers, lookback=252):
            super().__init__(ts)
            self.tickers = tickers
            self.lookback = lookback
            self.broker = ts.broker
            self.order_factory = ts.order_factory
            self.data_provider = ts.data_provider

        def calculate_and_place_orders(self):
            prices_df = self.data_provider.historical_price(
                self.tickers, PriceField.Close, self.lookback
            )

            prices_df.ffill(inplace=True)
            returns_df = prices_df.to_simple_returns()

            if len(returns_df) < 30:
                return  # not enough history yet

            cov_matrix = returns_df.cov()
            weights = MinVariancePortfolio(cov_matrix=cov_matrix).get_weights()

            # Build a {ticker: weight} dict and place target-percent orders
            target = {ticker: float(weights[ticker]) for ticker in self.tickers}
            orders = self.order_factory.target_percent_orders(target, MarketOrder(), TimeInForce.DAY)
            self.broker.cancel_all_open_orders()
            self.broker.place_orders(orders)


    def main():
        # settings
        backtest_name = 'MinVarianceStrategy'
        start_date = str_to_date("2010-01-01")
        end_date = str_to_date("2015-03-01")
        tickers = [DummyTicker('AAA'), DummyTicker('BBB'), DummyTicker('CCC'), DummyTicker('DDD')]

        # configuration
        settings = get_demo_settings()
        pdf_exporter = PDFExporter(settings)
        excel_exporter = ExcelExporter(settings)

        session_builder = BacktestTradingSessionBuilder(settings, pdf_exporter, excel_exporter)
        session_builder.set_frequency(Frequency.DAILY)
        session_builder.set_backtest_name(backtest_name)
        session_builder.set_data_provider(daily_data_provider)

        ts = session_builder.build(start_date, end_date)

        strategy = MinVarianceStrategy(ts, tickers)
        CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
        CalculateAndPlaceOrdersRegularEvent.exclude_weekends()
        strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

        ts.start_trading()

    if __name__ == '__main__':
        main()

