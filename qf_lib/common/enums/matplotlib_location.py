from enum import Enum


class Location(Enum):
    BEST = 0
    UPPER_RIGHT = 1
    UPPER_LEFT = 2
    LOWER_LEFT = 3
    LOWER_RIGHT = 4
    RIGHT = 5
    CENTER_LEFT = 6
    CENTER_RIGHT = 7
    LOWER_CENTER = 8
    UPPER_CENTER = 9
    CENTER = 10

    def __init__(self, code):
        self.code = code
