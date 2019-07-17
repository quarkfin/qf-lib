from datetime import datetime
from typing import Union

from pandas import DatetimeIndex, Timedelta, Index

from qf_lib.containers.series.qf_series import QFSeries


class ReturnsSeries(QFSeries):
    """
    Series of returns. It is a base class for series which specify the type of the returns (e.g. LogReturnsSeries).
    This is an abstract class and should not be instantiated.
    """

    @property
    def _constructor(self):
        raise NotImplementedError()

    @property
    def _constructor_expanddim(self):
        raise NotImplementedError()

    def to_log_returns(self):
        raise NotImplementedError()

    def to_simple_returns(self):
        raise NotImplementedError()

    def total_cumulative_return(self) -> float:
        raise NotImplementedError()

    def to_prices(self, initial_price: float = None, suggested_initial_date: Union[datetime, int, float] = None,
                  frequency=None) -> "PricesSeries":
        if suggested_initial_date is None:
            suggested_initial_date = self._get_initial_date(frequency)
        if initial_price is None:
            initial_price = 1.0

        if suggested_initial_date is not datetime:
            prices_dates = Index([suggested_initial_date]).append(self.index.copy())  # if it is numeric or string based
        else:
            prices_dates = DatetimeIndex([suggested_initial_date]).append(self.index.copy())

        prices_values = self._to_prices_values(initial_price)

        from qf_lib.containers.series.prices_series import PricesSeries
        return PricesSeries(data=prices_values, index=prices_dates).__finalize__(self)

    def _get_initial_date(self, frequency=None):
        if frequency is None:
            interval, _ = self.infer_interval()
        else:
            interval = Timedelta(frequency.nr_of_calendar_days(), unit='D')

        first_date = self.index[0]
        return first_date - interval

    def _to_prices_values(self, initial_price):
        # method must be implemented by classes inheriting from ReturnsSeries
        raise NotImplementedError()
