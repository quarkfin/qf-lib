from qf_lib.backtesting.execution_handler.simulated.commission_models.commission_model import CommissionModel
from qf_lib.backtesting.order.order import Order


class IBCommissionModel(CommissionModel):
    """
    Interactive Brokers commission for a transaction.

    This is based on the US Fixed pricing, the details of which can be found here:
    https://www.interactivebrokers.co.uk/en/index.php?f=1590&p=stocks1
    """

    def calculate_commission(self, order: Order, fill_price: float) -> float:
        quantity = abs(order.quantity)

        commission = min(
            0.01 * fill_price * quantity,
            max(1.0, 0.005 * quantity)
        )
        return commission
