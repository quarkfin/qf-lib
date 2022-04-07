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
import matplotlib.pyplot as plt

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from demo_scripts.demo_configuration.demo_data_provider import daily_data_provider
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.strategies.signal_generators import OnBeforeMarketOpenSignalGeneration

plt.ion()  # required for dynamic chart

from demo_scripts.backtester.moving_average_alpha_model import MovingAverageAlphaModel
from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.backtesting.strategies.alpha_model_strategy import AlphaModelStrategy
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


def main():
    start_date = str_to_date("2010-01-01")
    end_date = str_to_date("2015-03-01")

    # ----- build trading session ----- #
    session_builder: BacktestTradingSessionBuilder = container.resolve(BacktestTradingSessionBuilder)
    session_builder.set_frequency(Frequency.DAILY)
    session_builder.set_data_provider(daily_data_provider)
    session_builder.set_position_sizer(InitialRiskPositionSizer, initial_risk=0.05)

    ts = session_builder.build(start_date, end_date)

    model = MovingAverageAlphaModel(fast_time_period=5, slow_time_period=20, risk_estimation_factor=1.25,
                                    data_provider=ts.data_handler)
    model_tickers = [DummyTicker('AAA'), DummyTicker('BBB')]
    model_tickers_dict = {model: model_tickers}

    # ----- preload price data ----- #
    ts.use_data_preloading(model_tickers)

    # ----- start trading ----- #
    OnBeforeMarketOpenSignalGeneration(AlphaModelStrategy(ts, model_tickers_dict))
    ts.start_trading()


if __name__ == "__main__":
    main()
