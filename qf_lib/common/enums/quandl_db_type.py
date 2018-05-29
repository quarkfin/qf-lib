from enum import Enum


class QuandlDBType(Enum):
    Table = "Table"
    Timeseries = "Timeseries"

    @classmethod
    def list_members(cls):
        result = []
        for key, value in cls.__members__.items():
            result.append(str(value))
        return result

    def __str__(self):
        return str(self.value)

    def __lt__(self, other):
        # method required for grouping
        if self.__class__ is other.__class__:
            return self.value < other.value
        return False
