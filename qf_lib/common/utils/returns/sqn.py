from datetime import datetime

from qf_lib.common.enums.trade_field import TradeField
from qf_lib.common.utils.dateutils.to_days import to_days
from qf_lib.common.utils.miscellaneous.constants import DAYS_PER_YEAR_AVG
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame


def sqn(trades: QFDataFrame):
    """
    Calculates the simple SQN = mean return of trade / std(returns of trades)
    """

    returns = trades[TradeField.Return]
    result = returns.mean() / returns.std()
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


