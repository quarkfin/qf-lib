class Contract(object):
    def __init__(self, symbol: str, security_type: str, exchange: str):
        """
        Parameters
        ----------
        symbol
            symbol of the asset handled later on by the Broker (e.g. MSFT)
        security_type
            e.g. 'STK' for a stock
        exchange
            exchange on which the asset should be traded
        """
        self.symbol = symbol
        self.security_type = security_type
        self.exchange = exchange

    def __str__(self):
        return 'Contract: symbol: {}, security_type: {} exchange: {}'.format(
            self.symbol, self.security_type, self.exchange)

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Contract):
            return False

        return (self.symbol, self.security_type, self.exchange) == (other.symbol, other.security_type, other.exchange)

    def __hash__(self):
        return hash((self.symbol, self.security_type, self.exchange))
