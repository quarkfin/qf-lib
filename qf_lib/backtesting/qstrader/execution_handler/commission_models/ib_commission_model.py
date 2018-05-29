from qf_lib.backtesting.qstrader.execution_handler.commission_models.commission_model import CommissionModel


class IBCommissionModel(CommissionModel):
    """
    Interactive Brokers commission for a transaction.

    This is based on the US Fixed pricing, the details of which can be found here:
    https://www.interactivebrokers.co.uk/en/index.php?f=1590&p=stocks1
    """

    def calculate_commission(self, quantity, fill_price):
        commission = min(
            0.5 * fill_price * quantity,
            max(1.0, 0.005 * quantity)
        )
        return commission
