from enum import Enum


class TimeInForce(Enum):
    GTC = 1,
    """
    Order stays open until it is cancelled.
    """

    DAY = 2,
    """
    Order stays open for the rest of the day.
    """

    OPG = 3
    """
    Active ony on market open
    Combined with MarketOrder Creates Market On Open Order.
    """