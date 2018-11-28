from datetime import datetime, timedelta

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def sqn(trades: QFDataFrame):
    """
    Calculates the SQN = mean return of trade / std(returns of trades) * sqrt(100)
    """

    returns = trades[TradeField.Return]
    result = returns.mean() / returns.std() * 10
    return result


def avg_nr_of_trades_per1y(trades: QFDataFrame, start_date: datetime, end_date: datetime):
    """
    Calculates average number of trades per year for a given data-frame of trades.
    """
    returns = trades[TradeField.Return]
    period_length = end_date - start_date
    period_length_in_years = to_days(period_length) / DAYS_PER_YEAR_AVG
    avg_number_of_trades_1y = returns.count() / period_length_in_years
    return avg_number_of_trades_1y


def trade_based_cagr(trades: QFDataFrame, start_date: datetime, end_date: datetime):
    """
    Calculates average number of trades per year for a given data-frame of trades.
    """
    returns = trades[TradeField.Return]
    dates = trades[TradeField.EndDate]

    # insert start date and the beginning and end date at the end.
    # we insert nex start + 1day to returns and set the frequency for to_prices to daily so that the
    # prices series will start exactly from the start_date
    returns = pd.concat([pd.Series([0]), returns, pd.Series([0])])
    dates = pd.concat([pd.Series([start_date]), dates + timedelta(days=1), pd.Series([end_date])])

    returns_tms = SimpleReturnsSeries(index=dates, data=returns.values)
    prices_tms = returns_tms.to_prices(frequency=Frequency.DAILY)
    return cagr(prices_tms)


def trade_based_max_drawdown(trades: QFDataFrame):
    """
    Calculates the max drawdown on the series of returns of trades
    """
    returns = trades[TradeField.Return]
    dates = trades[TradeField.EndDate]
    returns_tms = SimpleReturnsSeries(index=dates, data=returns.values)
    return -max_drawdown(returns_tms)
