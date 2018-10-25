from enum import Enum


class TradeField(Enum):
    """
    Represents data fields that are properties of the trade
    """

    Ticker = 0
    StartDate = 1
    EndDate = 2
    Open = 3
    MaxGain = 4
    MinGain = 5
    Close = 6
    Return = 7
    Exposure = 8
