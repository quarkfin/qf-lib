from datetime import datetime

from qf_lib.backtesting.portfolio.portfolio import Portfolio


class BacktestResult(object):
    """
    BacktestResult is a class providing simple data model containing information about the backtest:
    for example it contains a portfolio with its timeseries and trades. It can also gather additional information
    """

    def __init__(self, portfolio: Portfolio, backtest_name: str=None,
                 start_date: datetime=None, end_date: datetime=None):
        self.portfolio = portfolio
        self.backtest_name = backtest_name
        self.start_date = start_date
        self.end_date = end_date
