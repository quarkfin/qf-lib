from enum import Enum


class RebaseMethod(Enum):
    # corresponds to: new_value = original_value / reference value
    divide = 1
    # corresponds to: new_value = original_value - reference value
    subtract = 2
    # corresponds to: new_value = original_value
    norebase = 3
