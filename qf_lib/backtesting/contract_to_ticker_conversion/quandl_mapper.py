from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.common.tickers.tickers import Ticker, QuandlTicker


class DummyQuandlContractTickerMapper(ContractTickerMapper):
    """
    Dummy QuandlTicker-Contract mapper.
    """
    def contract_to_ticker(self, contract: Contract, database_name: str='WIKI') -> Ticker:
        return QuandlTicker(ticker=contract.symbol, database_name=database_name)

    def ticker_to_contract(self, ticker: Ticker) -> Contract:
        return Contract(symbol=ticker.ticker, security_type='STK', exchange='SIMULATED_EXCHANGE')
