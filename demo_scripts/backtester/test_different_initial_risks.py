from time import time
from typing import List, Type

import numpy as np

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.alpha_model.all_tickers_used import get_all_tickers_used
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.alpha_model.alpha_model_strategy import AlphaModelStrategy
from qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats import InitialRiskStatsFactory
from qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator import ScenariosGenerator
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


def get_trade_rets_values(init_risk: float, alpha_model_type: Type[AlphaModel]) -> List[float]:
    start_date = str_to_date('2013-01-01')
    end_date = str_to_date('2016-12-31')

    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_position_sizer(InitialRiskPositionSizer, init_risk)
    session_builder.set_monitor_type(BacktestMonitor)
    session_builder.set_backtest_name("Initial Risk Testing - {}".format(init_risk))
    ts = session_builder.build(start_date, end_date)

    model_factory = AlphaModelFactory(ts.data_handler)
    model = model_factory.make_parametrized_model(alpha_model_type)
    model_tickers_dict = {model: [BloombergTicker('SVXY US Equity')]}

    AlphaModelStrategy(ts, model_tickers_dict, use_stop_losses=True)

    ts.use_data_preloading(get_all_tickers_used(model_tickers_dict))
    ts.start_trading()
    trades = ts.portfolio.get_trades()
    returns_of_trades = [(t.exit_price / t.entry_price - 1) * np.sign(t.quantity) for t in trades]
    return returns_of_trades


def main():
    alpha_model_type = None  # Set Alpha model that you wish to test
    stats_factory = InitialRiskStatsFactory(max_accepted_dd=0.1, target_return=0.02)
    initial_risks_list = [0.001, 0.005, 0.01, 0.02, 0.03, 0.05, 0.1]

    scenarios_generator = ScenariosGenerator()
    scenarios_df_list = []

    nr_of_param_sets = len(initial_risks_list)
    test_start_time = time()
    print("{} parameters sets to be tested".format(nr_of_param_sets))

    param_set_ctr = 1
    for init_risk in initial_risks_list:
        start_time = time()
        trade_rets_values = get_trade_rets_values(init_risk, alpha_model_type)
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
