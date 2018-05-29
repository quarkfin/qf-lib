from enum import Enum
from typing import List


class PriceField(Enum):
    """
    Represents one of the data fields that corresponds to OHLC and Volume.
    """

    Open = 1
    High = 2
    Low = 3
    Close = 4
    Volume = 5

    @staticmethod
    def ohlcv() -> List["PriceField"]:
        return [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close, PriceField.Volume]



