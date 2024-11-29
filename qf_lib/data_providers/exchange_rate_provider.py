from abc import ABCMeta, abstractmethod

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.tickers.tickers import Ticker


class ExchangeRateProvider(object, metaclass=ABCMeta):
    """
    An interface for providing exchange rates between currencies.
    """

    @abstractmethod
    def create_exchange_rate_ticker(self, base_currency: str, quote_currency: str) -> Ticker:
        pass

    @abstractmethod
    def get_last_available_exchange_rate(self, base_currency: str, quote_currency: str,
                                         frequency: Frequency = Frequency.DAILY):
        """
        Get last available exchange rate from the base currency to the quote currency in the provided frequency.

        Parameters
        -----------
        base_currency: str
            ISO code of the base currency (ex. 'USD' for US Dollar)
        quote_currency: str
            ISO code of the quote currency (ex. 'EUR' for Euro)
        frequency: Frequency
            frequency of the returned data

        Returns
        -------
        float
            last available exchange rate
        """
        pass
