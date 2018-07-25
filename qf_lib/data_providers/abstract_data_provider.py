from abc import ABCMeta

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.data_providers.price_data_provider import DataProvider


class AbstractDataProvider(DataProvider, metaclass=ABCMeta):
    """
    Creates an interface for data providers containing historical data of stocks, indices, futures
    and other asset classes. This is a base class of any simple data provider (a data provider that is associated with
    single data base, for example: Quandl, Bloomberg, Yahoo.)
    """

    @staticmethod
    def _is_single_ticker(value):
        if isinstance(value, Ticker):
            return True

        return False

    @staticmethod
    def _is_single_date(start_date, end_date):
        return start_date is not None and (start_date == end_date)
