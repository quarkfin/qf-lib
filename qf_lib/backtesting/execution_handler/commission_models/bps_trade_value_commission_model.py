from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.order.order import Order


class BpsTradeValueCommissionModel(CommissionModel):
    """
    Commission model which uses fixed bps rate for trade value. For example always 2pbs of the $ value ot the trade.
    """
    def __init__(self, commission: float):
        """
        Parameters
        ----------
        commission
            commission expressed in a basis points. (e.g. 2.0 denotes 2 pbs of trade value).
        """
        self.commission = commission

    def calculate_commission(self, order: Order, fill_price: float) -> float:
        quantity = abs(order.quantity)
        commission = fill_price * quantity * self.commission / 10000
        return commission
