from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker, BloombergTicker


class VolStrategyContractTickerMapper(ContractTickerMapper):
    """
    Contract Ticker Mapper that works only for one ticker - SVXY
    """

    symbol = "SVXY"
    bbg_suffix = "US Equity"
    sec_type = "STK"
    bbg_ticker_str = "{} {}".format(symbol, bbg_suffix)

    def contract_to_ticker(self, contract: Contract) -> Ticker:
        assert contract.symbol == self.symbol
        assert contract.security_type == self.sec_type
        return BloombergTicker(self.bbg_ticker_str)

    def ticker_to_contract(self, ticker: BloombergTicker) -> Contract:
        assert ticker.ticker == self.bbg_ticker_str
        return Contract(symbol=self.symbol, security_type=self.sec_type, exchange="ARCA")
