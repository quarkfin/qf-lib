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
from datetime import datetime
from typing import List, Tuple

from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.signals.signals_register import SignalsRegister
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class BacktestSignalsRegister(SignalsRegister):
    """ In memory implementation of Signals Register. """
    def __init__(self):
        self._signals_data = []  # type: List[Tuple[datetime, str, Signal]]

    def save_signals(self, signals: List[Signal]):
        """
        Add the provided signals to the list of all cached signals.
        """
        self._signals_data.extend(
            ((signal.creation_time, self._generate_ticker_name(signal), signal) for signal in signals)
        )

    def get_signals(self) -> QFDataFrame:
        df = QFDataFrame.from_records(self._signals_data, columns=["Date", "Ticker", "Signal"])

        # Modify the dataframe to move all signals for certain tickers to separate columns and set the index to date
        df = df.pivot_table(index='Date', columns='Ticker', values='Signal', aggfunc='first')
        return QFDataFrame(df)

    def get_signals_for_ticker(self, ticker: Ticker, alpha_model=None) -> QFSeries:
        def signal_to_return(signal: Signal):
            if alpha_model is None:
                return signal.ticker == ticker
            else:
                return signal.ticker == ticker and str(signal.alpha_model) == str(alpha_model)

        signals_data_for_ticker = [(d, s) for (d, _, s) in self._signals_data if signal_to_return(s)]

        df = QFDataFrame.from_records(signals_data_for_ticker, columns=["Date", "Signal"])
        df = df.set_index("Date").sort_index()
        series = df.iloc[:, 0]
        return series
