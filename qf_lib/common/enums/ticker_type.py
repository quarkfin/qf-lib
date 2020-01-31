from enum import Enum


class TickerType(Enum):
    Bloomberg = 0
    Quandl = 1
    InternalID = 2
    InternalName = 3

    @classmethod
    def list_members(cls):
        result = []
        for key, value in cls.__members__.items():
            result.append(str(value))
        return result
