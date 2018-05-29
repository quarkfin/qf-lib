from enum import Enum


class OptionType(Enum):
    Put = 0
    Call = 1

    def to_short_string(self) -> str:
        if self == OptionType.Call:
            return "C"
        if self == OptionType.Put:
            return "P"
        return None
