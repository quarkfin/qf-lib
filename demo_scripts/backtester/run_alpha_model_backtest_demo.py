import matplotlib.pyplot as plt

from demo_scripts.backtester.moving_average_alpha_model import MovingAverageAlphaModel
from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.execution_handler.simulated.commission_models.ib_commission_model import IBCommissionModel
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.monitoring.past_signals_generator import get_all_tickers_used

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports

from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.backtesting.strategy.trading_strategy import TradingStrategy
from qf_lib.backtesting.alpha_models_testers.alpha_model_factory import AlphaModelFactory
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


def main():
    model_type = MovingAverageAlphaModel

    initial_risk = 0.03
    commission_model = IBCommissionModel()

    start_date = str_to_date('2016-01-01')
    end_date = str_to_date('2018-12-31')

    # ----- build trading session ----- #
    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_backtest_name('Moving Average Alpha Model Backtest')
    session_builder.set_position_sizer(InitialRiskPositionSizer, initial_risk)
    session_builder.set_commission_model(commission_model)
    session_builder.set_monitor_type(BacktestMonitor)
    ts = session_builder.build(start_date, end_date)

    # ----- build models ----- #
    model_factory = AlphaModelFactory(ts.data_handler)
    model = model_factory.make_parametrized_model(model_type)
    model_tickers = [BloombergTicker('AAPL US Equity'), BloombergTicker('FB US Equity')]
    model_tickers_dict = {model: model_tickers}

    # ----- preload price data ----- #
    all_tickers_used = get_all_tickers_used(model_tickers_dict)
    ts.use_data_preloading(all_tickers_used)

    # ----- start trading ----- #
    TradingStrategy(ts, model_tickers_dict, use_stop_losses=True)
    ts.start_trading()

    # ----- use results ----- #
    backtest_tms = ts.portfolio.get_portfolio_timeseries().to_log_returns()
    print("mean daily log return: {}".format(backtest_tms.mean()))
    print("std of daily log returns: {}".format(backtest_tms.std()))


if __name__ == "__main__":
    main()
