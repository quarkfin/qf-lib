from datetime import datetime
from typing import Sequence

from qf_lib.backtesting.qstrader.events.event_base import Event
from qf_lib.backtesting.qstrader.order.order import Order
from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class SignalEvent(Event):
    """
    Handles the event of sending a Signal from a Strategy object.
    This is received by a Portfolio object and acted upon.
    """
    def __init__(self, time: datetime, suggested_orders: Sequence[Order]) -> None:
        """
        Parameters
        ----------
        time
            time at which the signal was generated
        suggested_orders
            list of suggested Orders (each Order can be sized by PositionSizer and cut or even rejected by RiskManager)
        """
        super().__init__(time)
        self.suggested_orders = suggested_orders

    def __str__(self):
        return_string = "{} - {:<25} -> Orders:".format(date_to_str(self.time), self.__class__.__name__)
        if self.suggested_orders:
            for order in self.suggested_orders:
                return_string += "\n{}".format(order)
        else:
            return_string += "Empty order list"

        return return_string
