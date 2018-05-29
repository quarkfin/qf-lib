from qf_lib.backtesting.qstrader.execution_handler.commission_models.commission_model import CommissionModel


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

    def calculate_commission(self, quantity, fill_price):
        return self.commission
