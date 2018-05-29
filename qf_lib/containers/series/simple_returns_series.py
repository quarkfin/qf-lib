from numpy import log, append

from qf_lib.containers.series.returns_series import ReturnsSeries


class SimpleReturnsSeries(ReturnsSeries):
    """
    Series of log-returns.
    """

    @property
    def _constructor(self):
        return SimpleReturnsSeries

    @property
    def _constructor_expanddim(self):
        from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
        return SimpleReturnsDataFrame

    def to_log_returns(self):
        from qf_lib.containers.series.log_returns_series import LogReturnsSeries
        log_returns_values = [log(simple_ret + 1) for simple_ret in self.values]
        log_returns_tms = LogReturnsSeries(index=self.index.copy(), data=log_returns_values).__finalize__(self)

        return log_returns_tms

    def to_simple_returns(self):
        return self

    def total_cumulative_return(self) -> float:
        return (self + 1.0).prod() - 1.0

    def _to_prices_values(self, initial_price):
        prices_values = append([1], self.values + 1)
        prices_values = prices_values.cumprod()

        return prices_values * initial_price
