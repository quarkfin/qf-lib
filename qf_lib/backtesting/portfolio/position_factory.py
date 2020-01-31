from datetime import datetime

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.backtest_equity_position import BacktestEquityPosition
from qf_lib.backtesting.portfolio.backtest_future_position import BacktestFuturePosition
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition


class BacktestPositionFactory(object):

    @staticmethod
    def create_position(contract: Contract, creation_time: datetime) -> BacktestPosition:
        """
        Creates a backtest position according to the asset class (security_type) of the security
        as defined in the Contract
        """
        sec_type = contract.security_type
        if sec_type == 'STK':
            return BacktestEquityPosition(contract, creation_time)
        elif sec_type == 'FUT':
            return BacktestFuturePosition(contract, creation_time)
        else:
            raise ValueError("Contract security type: '{}' not correct. Use 'STK' or  'FUT' ".format(sec_type))
