from qf_lib.backtesting.execution_handler.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.order.order import Order


class FixedCommissionModel(CommissionModel):
    """
    Naive commission model which always charges the same commission.
    """

    def __init__(self, commission: float):
        """
        Parameters
        ----------
        commission
            commission expressed in a currency of a traded asset (e.g. 1.0 could denote 1.0 USD).
        """
        self.commission = commission

    def calculate_commission(self, order: Order, fill_price: float) -> float:
        return self.commission
