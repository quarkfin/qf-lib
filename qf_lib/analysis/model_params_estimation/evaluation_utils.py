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
from collections import defaultdict
from datetime import datetime
from math import sqrt
from typing import Sequence

from qf_lib.backtesting.fast_alpha_model_tester.backtest_summary import BacktestSummary
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.returns.sqn import avg_nr_of_trades_per1y, sqn
from qf_lib.containers.series.qf_series import QFSeries


class BacktestSummaryEvaluator:
    def __init__(self, backtest_summary: BacktestSummary):
        self.backtest_summary = backtest_summary

        self.params_backtest_summary_elem_dict = defaultdict(list)
        for elem in backtest_summary.elements_list:
            self.params_backtest_summary_elem_dict[elem.model_parameters].append(elem)

    def evaluate_params_for_tickers(self, parameters: tuple, tickers: Sequence[Ticker], start_time: datetime,
                                    end_date: datetime):

        # Get the backtest element for the given list of tickers
        backtest_elements_for_tickers = [el for el in self.params_backtest_summary_elem_dict[parameters]
                                         if set(el.tickers) == set(tickers)]
        assert len(backtest_elements_for_tickers) == 1, "Check if the modeled_params passed to " \
                                                        "FastAlphaModelTesterConfig match those you want to test"
        backtest_elem = backtest_elements_for_tickers[0]
        returns_tms = backtest_elem.returns_tms.dropna(how="all")
        trades = backtest_elem.trades

        # Create the TradesEvaluationResult object
        ticker_evaluation = TradesEvaluationResult()
        ticker_evaluation.ticker = tickers
        ticker_evaluation.parameters = parameters
        ticker_evaluation.end_date = end_date
        # Compute the start date as the maximum value between the given start_time and the first date of returns tms in
        # case of 1 ticker backtest
        if len(tickers) == 1:
            start_date = max(start_time, returns_tms.index[0]) if not returns_tms.empty else end_date
        else:
            start_date = start_time
        ticker_evaluation.start_date = start_date

        if start_date >= end_date:
            # Do not compute further fields - return the default None values
            return ticker_evaluation

        avg_nr_of_trades = avg_nr_of_trades_per1y(QFSeries([t for t in trades if t.start_time >= start_date
                                                            and t.end_time <= end_date]), start_date, end_date)
        ticker_evaluation.avg_nr_of_trades_1Y = avg_nr_of_trades
        ticker_evaluation.sqn_per_avg_nr_trades = sqn(QFSeries([t.pnl for t in trades if t.start_time >= start_date
                                                                and t.end_time <= end_date])) * sqrt(avg_nr_of_trades)

        returns_tms = returns_tms.loc[start_date:end_date]
        if not returns_tms.empty:
            ticker_evaluation.annualised_return = cagr(returns_tms, Frequency.DAILY)

        return ticker_evaluation


class TradesEvaluationResult:
    def __init__(self):
        self.ticker = None
        self.parameters = None

        self.sqn_per_avg_nr_trades = None
        self.avg_nr_of_trades_1Y = None
        self.annualised_return = None

        self.start_date = None
        self.end_date = None
