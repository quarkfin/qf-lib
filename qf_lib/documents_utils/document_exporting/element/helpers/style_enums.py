from enum import Enum


class DataType(Enum):
    ROW = 1
    COLUMN = 2
    INDEX = 3
    CELL = 4
    TABLE = 5
    HEADER = 6


class StylingType(Enum):
    STYLE = 1
    CLASS = 2
