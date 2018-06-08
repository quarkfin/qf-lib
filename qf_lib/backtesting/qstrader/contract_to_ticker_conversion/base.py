from abc import ABCMeta, abstractmethod

from qf_lib.backtesting.qstrader.contract.contract import Contract
from qf_lib.common.tickers.tickers import Ticker


class ContractTickerMapper(metaclass=ABCMeta):
    @abstractmethod
    def contract_to_ticker(self, contract: Contract) -> Ticker:
        pass

    @abstractmethod
    def ticker_to_contract(self, ticker: Ticker) -> Contract:
        pass
