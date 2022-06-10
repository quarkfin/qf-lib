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

"""
This module presents an example of a strategy, which every minutes computes two simple moving averages
(long - 20 minutes, short - 5 minutes) every 15 minutes, between 10:00 and 13:00, and creates a buy order in case
if the short moving average is greater or equal to the long moving average.

The strategy uses PortaraDataProvider with 1-minute frequency bars.
"""


import logging
from os import path

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from demo_scripts.strategies.intraday_strategy import IntradayMAStrategy
from qf_lib.backtesting.events.time_event.periodic_event.calculate_and_place_orders_event import \
    CalculateAndPlaceOrdersPeriodicEvent
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import PortaraTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.logging.logging_config import setup_logging
from qf_lib.containers.futures.future_tickers.portara_future_ticker import PortaraFutureTicker
from qf_lib.data_providers.portara.portara_data_provider import PortaraDataProvider

plt.ion()  # required for dynamic chart, good to keep this at the beginning of imports


def main(path_to_data_files: str, ticker: PortaraTicker):
    """
    In order to run the example you need to provide the path to the top directory, containing your data files. The
    example below will download Open, High, Low and Close Prices along with Volume for the given (future) ticker.

    Notes
    ---------
    The two files containing data for the ticker should have the same name as the tickers that you are passing as the
    parameter. For example - to run the example below, you will need to save prices of the data as VE.csv and WEAT.csv.

    Parameters
    -----------
    path_to_data_files: str
        path to the top directory, which contains all your Portara data files
    ticker: PortaraTicker
        ticker for which the data will be downloaded
    """

    backtest_name = 'Intraday Strategy Demo Using Portara'
    data_start_date = str_to_date("2019-01-01")
    start_date = str_to_date("2019-01-05")
    end_date = str_to_date("2019-01-20 23:59:00.0", DateFormat.FULL_ISO)

    setup_logging(logging.INFO, console_logging=True)

    if ticker is None or not path.exists(path_to_data_files):
        raise ValueError(f"Check if correct Ticker is set and corresponding Portara file is placed in "
                         f"{path_to_data_files}")

    data_provider = PortaraDataProvider(path_to_data_files, ticker, PriceField.ohlcv(), data_start_date, end_date,
                                        Frequency.MIN_1)

    session_builder = container.resolve(BacktestTradingSessionBuilder)  # type: BacktestTradingSessionBuilder
    session_builder.set_frequency(Frequency.MIN_1)
    session_builder.set_market_open_and_close_time({"hour": 9, "minute": 15}, {"hour": 13, "minute": 15})
    session_builder.set_backtest_name(backtest_name)
    session_builder.set_data_provider(data_provider)

    ts = session_builder.build(start_date, end_date)

    # If the ticker is a future ticker - initialize the data provider
    if isinstance(ticker, PortaraFutureTicker):
        ticker.initialize_data_provider(ts.timer, ts.data_provider)

    strategy = IntradayMAStrategy(ts, ticker)

    # Compute the signals and place orders every 15 minutes between 10 and 13
    CalculateAndPlaceOrdersPeriodicEvent.set_frequency(Frequency.MIN_15)
    CalculateAndPlaceOrdersPeriodicEvent.set_start_and_end_time(
        {"hour": 10, "minute": 0},
        {"hour": 13, "minute": 0})
    strategy.subscribe(CalculateAndPlaceOrdersPeriodicEvent)

    ts.start_trading()

    backtest_tms = ts.portfolio.portfolio_eod_series().to_log_returns()
    print("mean daily log return: {}".format(backtest_tms.mean()))
    print("std of daily log returns: {}".format(backtest_tms.std()))


if __name__ == "__main__":
    # Download the data and assign the path to the directory with your files to the path_to_data_files variable
    path_to_data_files = None
    # Choose the ticker to use for the backtest, e.g.
    # ticker = PortaraFutureTicker('Silver', 'SIA{}', 1, 1, 50, designated_contracts="HKNUZ")
    ticker = None
    main(path_to_data_files, ticker)
