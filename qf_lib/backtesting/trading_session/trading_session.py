from abc import ABCMeta, abstractmethod


class TradingSession(object, metaclass=ABCMeta):
    """
    Base class for all Trading Sessions. It configures all the elements of the trading environment.
    """

    @abstractmethod
    def start_trading(self) -> None:
        """
        Run this method in order to perform all the trading activities
        """
