from time import time
from typing import List

import numpy as np

from geneva_analytics.backtesting.alpha_models.vol_long_short.vol_long_short import VolLongShort
from qf_common.config.ioc import container
from qf_lib.backtesting.alpha_models_testers.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.alpha_models_testers.initial_risk_stats import InitialRiskStatsFactory
from qf_lib.backtesting.alpha_models_testers.scenarios_generator import ScenariosGenerator
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.strategy.trading_strategy import TradingStrategy
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


def calc_trade_returns(trades):
    return [(t.exit_price / t.entry_price - 1) * np.sign(t.quantity) for t in trades]


def get_trade_rets_values(init_risk: float) -> List[float]:
    model_type = VolLongShort
    param_set = (4.5, 2, 4)
    stop_loss_param = 1.25

    trading_tickers = [
        # BloombergTicker('VXX US Equity'),
        BloombergTicker('SVXY US Equity')
    ]

    # if some additional data is needed, the extra tickers should be specified below; if not, leave empty:
    data_tickers = [
        BloombergTicker('SPX Index'),
        BloombergTicker('VIX Index')
    ]

    start_date = str_to_date('2013-01-01')
    end_date = str_to_date('2016-12-31')

    session_builder = BacktestTradingSessionBuilder(start_date, end_date)
    session_builder.set_alpha_model_backtest_name(model_type, param_set, trading_tickers)
    session_builder.set_intial_risk_position_sizer(init_risk)
    session_builder.set_monitor_type(BacktestMonitor)
    session_builder.set_backtest_name("Initial Risk Testing - {}".format(init_risk))
    ts = session_builder.build(container)
    session_builder.use_data_preloading(trading_tickers + data_tickers)

    model_factory = AlphaModelFactory(ts.data_handler)
    model = model_factory.make_model(model_type, *param_set, risk_estimation_factor=stop_loss_param)

    TradingStrategy(ts, [model], trading_tickers, use_stop_losses=True)
    ts.start_trading()
    trades = ts.portfolio.get_trades()
    return calc_trade_returns(trades)


def main():
    scenarios_generator = ScenariosGenerator()
    stats_factory = InitialRiskStatsFactory(max_accepted_dd=0.1, target_return=0.02)
    initial_risks_list = [0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1]

    scenarios_df_list = []

    nr_of_param_sets = len(initial_risks_list)
    test_start_time = time()
    print("{} parameters sets to be tested".format(nr_of_param_sets))

    param_set_ctr = 1
    for init_risk in initial_risks_list:
        start_time = time()
        trade_rets_values = get_trade_rets_values(init_risk)
        scenarios_df = scenarios_generator.make_scenarios(
            trade_rets_values, scenarios_length=100, num_of_scenarios=10000
        )

        end_time = time()
        print("{} / {} initial risk parameters tested".format(param_set_ctr, nr_of_param_sets))
        print("iteration time = {:5.2f} minutes".format((end_time - start_time) / 60))
        param_set_ctr += 1

        scenarios_df_list.append(scenarios_df)

    print("\nGenerating stats...")
    start_time = time()

    stats = stats_factory.make_stats(initial_risks_list, scenarios_df_list)
    print(stats)

    end_time = time()
    print("iteration time = {:5.2f} minutes".format((end_time - start_time) / 60))

    test_end_time = time()
    print("test duration time = {:5.2f} minutes".format((test_end_time - test_start_time) / 60))


if __name__ == '__main__':
    main()
