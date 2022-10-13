#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from time import time
from typing import List

from demo_scripts.backtester.moving_average_alpha_model import MovingAverageAlphaModel
from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.events.time_event.regular_time_event.calculate_and_place_orders_event import \
    CalculateAndPlaceOrdersRegularEvent
from qf_lib.backtesting.fast_alpha_model_tester.initial_risk_stats import InitialRiskStatsFactory
from qf_lib.backtesting.fast_alpha_model_tester.scenarios_generator import ScenariosGenerator
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitorSettings
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.strategies.alpha_model_strategy import AlphaModelStrategy
from qf_lib.backtesting.trading_session.backtest_trading_session import BacktestTradingSession
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.starting_dir import set_starting_dir_abs_path


def _create_trading_session(init_risk: float):
    start_date = str_to_date('2016-01-01')
    end_date = str_to_date('2017-12-31')

    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_data_provider(daily_data_provider)
    session_builder.set_position_sizer(InitialRiskPositionSizer, initial_risk=init_risk)
    session_builder.set_monitor_settings(BacktestMonitorSettings.no_stats())
    session_builder.set_backtest_name("Initial Risk Testing - {}".format(init_risk))
    session_builder.set_frequency(Frequency.DAILY)
    ts = session_builder.build(start_date, end_date)
    return ts


def get_trade_rets_values(ts: BacktestTradingSession, model: AlphaModel) -> List[float]:
    model_tickers_dict = {model: [DummyTicker('BBB')]}

    strategy = AlphaModelStrategy(ts, model_tickers_dict, use_stop_losses=True)

    CalculateAndPlaceOrdersRegularEvent.set_daily_default_trigger_time()
    strategy.subscribe(CalculateAndPlaceOrdersRegularEvent)

    ts.start_trading()

    trades_generator = TradesGenerator()
    positions = ts.portfolio.closed_positions()
    portfolio_values = ts.portfolio.portfolio_eod_series()
    trades = trades_generator.create_trades_from_backtest_positions(positions, portfolio_values)
    returns_of_trades = [t.percentage_pnl for t in trades]
    return returns_of_trades


def main():
    # set the starting directory path below unless you set environment variable QF_STARTING_DIRECTORY to proper value
    # set_starting_dir_abs_path(r"absolute/path/to/qf-lib")
    set_starting_dir_abs_path(r"C:\Development\qf-lib")

    stats_factory = InitialRiskStatsFactory(max_accepted_dd=0.3, target_return=0.1)
    initial_risks_list = [0.001, 0.005, 0.01, 0.02, 0.05]

    scenarios_generator = ScenariosGenerator()
    scenarios_df_list = []

    nr_of_param_sets = len(initial_risks_list)
    test_start_time = time()
    print("{} parameters sets to be tested".format(nr_of_param_sets))

    param_set_ctr = 1
    for init_risk in initial_risks_list:
        start_time = time()
        ts = _create_trading_session(init_risk)
        alpha_model = MovingAverageAlphaModel(10, 30, 2, ts.data_provider)  # Alpha model that is being tested
        trade_rets_values = get_trade_rets_values(ts, alpha_model)
        scenarios_df = scenarios_generator.make_scenarios(
            trade_rets_values, scenarios_length=100, num_of_scenarios=1000
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
