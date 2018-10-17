from enum import Enum


class TradeField(Enum):
    """
    Represents data fields that are properties of the trade
    """

    StartDate = 1
    EndDate = 2
    Open = 3
    High = 4
    Low = 5
    Close = 6
    Return = 7
    Exposure = 8

