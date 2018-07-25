from abc import ABCMeta

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.price_data_provider import DataProvider


class AbstractDataProvider(DataProvider, metaclass=ABCMeta):
    """
    Creates an interface for data providers containing historical data of stocks, indices, futures
    and other asset classes. This is a base class of any simple data provider (a data provider that is associated with
    single data base, for example: Quandl, Bloomberg, Yahoo.)
    """

    @staticmethod
    def _cast_result_to_proper_type(result):
        num_of_dimensions = len(result.axes)
        if num_of_dimensions == 1:
            casted_result = cast_series(result, QFSeries)
        elif num_of_dimensions == 2:
            casted_result = cast_dataframe(result, QFDataFrame)
        else:
            casted_result = result

        return casted_result

    @staticmethod
    def _is_single_ticker(value):
        if isinstance(value, Ticker):
            return True

        return False

    @staticmethod
    def _is_single_date(start_date, end_date):
        return start_date is not None and (start_date == end_date)
