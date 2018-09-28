from enum import Enum


class TimeInForce(Enum):
    GTC = 1,
    """
    Order stays open until it is cancelled.
    """

    DAY = 2
    """
    Order stays open for the rest of the day.
    """
