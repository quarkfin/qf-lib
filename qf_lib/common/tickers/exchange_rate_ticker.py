from qf_lib.common.tickers.tickers import Ticker


class CurrencyExchangeTicker():
    """Ticker representing a foreign exchange rate from a base currency to a quote currency.

    Parameters
    ----------
    ticker: Ticker
        Ticker of the security in a specific database.
    base_currency: str
        The ISO code of the base currency in the exchange rate (ex. 'USD' for US Dollar).
    quote_currency: str
        The ISO code of the quote currency in the exchange rate.
    quote_factor: int
        Used to define the size of the contract.

    """
    def __init__(self, ticker: Ticker, base_currency: str, quote_currency: str, quote_factor: int = 1):
        self.ticker = ticker
        self.base_currency = base_currency
        self.quote_currency = quote_currency
        self.quote_factor = quote_factor
