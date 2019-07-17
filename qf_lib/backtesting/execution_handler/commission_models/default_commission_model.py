from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.order.order import Order


class DefaultCommissionModel(CommissionModel):
    """
    Naive commission model which always charges the same commission.
    """
    commission = 2.25  # expressed in bps of the total value of the trade

    def calculate_commission(self, order: Order, fill_price: float) -> float:
        quantity = abs(order.quantity)
        commission = fill_price * quantity * self.commission / 10000
        return commission
