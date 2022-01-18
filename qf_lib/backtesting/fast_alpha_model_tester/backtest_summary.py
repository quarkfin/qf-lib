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
from typing import Tuple, Sequence, Type, List

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.portfolio.trade import Trade
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class BacktestSummaryElement:
    """Class containing a summary of the performed backtest.

    Parameters
    ----------
    model_parameters: Tuple
        Parameters of the model (e.g. length of moving averages).
    model_parameters_names: Tuple[str]
        Names of the parameters of the model.
    returns_tms: SimpleReturnsSeries
        SimpleReturnsSeries of the Portfolio.
    trades: Sequence[Trade]
        Sequence of Trades (groups of Transactions) performed by the tested strategy.
    tickers: Sequence[Ticker]
        Sequence of Tickers for which the single backtest was performed.
    """
    def __init__(self, model_parameters: Tuple, model_parameters_names: Tuple[str], returns_tms: SimpleReturnsSeries,
                 trades: Sequence[Trade], tickers: Sequence[Ticker]):
        self.model_parameters = model_parameters
        self.model_parameters_names = model_parameters_names
        self.returns_tms = returns_tms
        self.trades = trades
        self.tickers = tickers


class BacktestSummary:
    def __init__(self, tickers: Sequence[Ticker], alpha_model_type: Type[AlphaModel],
                 elements_list: Sequence[BacktestSummaryElement], start_date: datetime, end_date: datetime):
        self.tickers = tickers
        self.alpha_model_type = alpha_model_type
        self.elements_list = elements_list
        self.asset_class = None
        self.start_date = start_date
        self.end_date = end_date

    @property
    def num_of_model_params(self) -> int:
        params_lengths_list = [len(elem.model_parameters) for elem in self.elements_list]
        first_param_set_length = params_lengths_list[0]

        all_elements_in_the_list_are_equal = all(
            (param_sets_length == first_param_set_length for param_sets_length in params_lengths_list))
        assert all_elements_in_the_list_are_equal

        return first_param_set_length

    @property
    def backtest_name(self) -> str:
        if self.asset_class is not None:
            return "{} - {}".format(self.asset_class, self.alpha_model_type.__name__)
        return self.alpha_model_type.__name__

    @property
    def parameters_tested(self) -> List[List[float]]:
        result = []
        for i in range(self.num_of_model_params):
            inner_list = [elem.model_parameters[i] for elem in self.elements_list]
            result.append(sorted(list(set(inner_list))))
        return result
