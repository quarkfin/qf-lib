import datetime

from numpy.ma import log

from qf_lib.containers.series.qf_series import QFSeries


class PricesSeries(QFSeries):
    """
    Series of prices (e.g. prices of the SPY).
    """

    def __init__(self, data=None, index=None, dtype=None, name=None, copy=False, fastpath=False):
        super().__init__(data, index, dtype, name, copy, fastpath)

    @property
    def _constructor(self):
        return PricesSeries

    @property
    def _constructor_expanddim(self):
        from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
        return PricesDataFrame

    def to_log_returns(self) -> "LogReturnsSeries":
        from qf_lib.containers.series.log_returns_series import LogReturnsSeries

        return_values = []

        for i in range(1, len(self)):
            return_value = log(self[i] / self[i - 1])
            return_values.append(return_value)

        dates = self.index[1::].copy()

        return LogReturnsSeries(index=dates, data=return_values).__finalize__(self)

    def to_simple_returns(self) -> "SimpleReturnsSeries":
        from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries

        return_values = []

        for i in range(1, len(self)):
            return_value = self[i] / self[i - 1] - 1
            return_values.append(return_value)

        dates = self.index[1::].copy()

        return SimpleReturnsSeries(index=dates, data=return_values).__finalize__(self)

    def to_prices(self, initial_price: float = None, suggested_initial_date: datetime = None, frequency=None) \
            -> ["PricesSeries"]:
        if initial_price is None:
            return self.copy()

        return self / self[0] * initial_price

    def total_cumulative_return(self) -> float:
        return self.values[-1] / self.values[0] - 1.0
