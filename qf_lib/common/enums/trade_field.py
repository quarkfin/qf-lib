from enum import Enum


class TradeField(Enum):
    """
    Represents data fields that are properties of the Trade.
    """

    Ticker = 0
    """
    The Ticker which was traded in the Trade.
    """

    StartDate = 1
    """
    Date when the Trade was entered.
    """

    EndDate = 2
    """
    Date when the Trade was closed.
    """

    Open = 3
    """
    Price at which the Trade was entered (opened).
    """

    MaxGain = 4
    """
    Maximum difference between the value of the Trade and the price at which the Trade was entered.
    Can be 0.0 if the Trade was only loosing a value. Expressed in currency units (e.g. 1200.0).
    """

    MaxLoss = 5
    """
    Maximum negative difference between the value of the Trade and the price at which the Trade was entered.
    It's always negative. Can be 0.0 if the Trade was only gaining a value. Expressed in currency units (e.g. -100.0).
    """

    Close = 6
    """
    Price at which the Trade was exited (closed).
    """

    Return = 7
    """
    Arithmetic return on the Trade (Close/Open - 1 for the Long Trade and 1 - Close/Open for the Short Trade).
    """

    Exposure = 8
    """
    1.0 for the Long Trade and -1.0 for the Short Trade.
    """
