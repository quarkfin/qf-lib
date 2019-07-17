from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker, BloombergTicker


class IB_Bloomberg_ContractTickerMapper(ContractTickerMapper):
    """
    BloombergTicker- IB Contract mapper that can be used for live trading.
    It is using the "SMART" exchange for all products
    """

    def __init__(self, bbg_suffix: str, security_type: str):
        """
        bbg_suffix:
            is the suffix added after the first part of the BBG ticker.
            For example: "US Equity", "PW Equity", etc
        security_type:
            corresponds to the security type that is used to create Contract.
            For example: use "STK" for stocks, ETFs and ETNs,
                         use "CMDTY" for commodities,
                         use "BOND" for bonds
                         use "OPT" for options
                         use "FUT" for futures
        """
        self.bbg_suffix = bbg_suffix
        self.security_type = security_type

    def contract_to_ticker(self, contract: Contract) -> Ticker:
        return BloombergTicker(ticker=contract.symbol)

    def ticker_to_contract(self, ticker: BloombergTicker) -> Contract:
        split_ticker = ticker.ticker.split()
        return Contract(symbol=split_ticker[0], security_type=self.security_type, exchange="SMART")
