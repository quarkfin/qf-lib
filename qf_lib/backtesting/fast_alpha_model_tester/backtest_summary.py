from datetime import datetime
from typing import Tuple, Sequence, Type, List

import pandas as pd

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


class BacktestSummaryElement(object):
    def __init__(self, model_parameters: Tuple, returns_tms: SimpleReturnsSeries, trades_df: pd.DataFrame):
        """
        Parameters
        ----------
        model_parameters
            Parameters of the model (e.g. length of moving averages).
        returns_tms
            SimpleReturnsSeries of the Portfolio.
        trades_df
            DataFrame representing Trades (pairs of Transactions) performed by the tested strategy. Rows are indexed
            with natural numbers (starting with 0). Columns are indexed with TradeFields (see: TradeField).
            If there are multiple tickers, then there will be one row for each position opened and then closed.
        """
        self.model_parameters = model_parameters
        self.returns_tms = returns_tms
        self.trades_df = trades_df


class BacktestSummary(object):
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
