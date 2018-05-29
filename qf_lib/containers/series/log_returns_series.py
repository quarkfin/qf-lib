import numpy as np
from numpy.ma import exp, append

from qf_lib.containers.series.returns_series import ReturnsSeries


class LogReturnsSeries(ReturnsSeries):
    """
    Series of log-returns.
    """

    @property
    def _constructor(self):
        return LogReturnsSeries
    
    @property
    def _constructor_expanddim(self):
        from qf_lib.containers.dataframe.log_returns_dataframe import LogReturnsDataFrame
        return LogReturnsDataFrame

    def to_log_returns(self):
        return self

    def to_simple_returns(self):
        from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries

        simple_rets_values = [exp(log_ret) - 1 for log_ret in self.values]
        simple_returns_tms = SimpleReturnsSeries(index=self.index.copy(), data=simple_rets_values).__finalize__(self)

        return simple_returns_tms

    def total_cumulative_return(self) -> float:
        return np.exp(self.sum()) - 1.0

    def _to_prices_values(self, initial_price):
        prices_values = self.values.cumsum()
        prices_values = exp(prices_values)
        prices_values = append([1], prices_values)

        return prices_values * initial_price
