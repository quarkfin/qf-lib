from enum import Enum


class GridProportion(Enum):
    One = "one"
    Two = "two"
    Three = "three"
    Four = "four"
    Five = "five"
    Six = "six"
    Seven = "seven"
    Eight = "eight"
    Nine = "nine"
    Ten = "ten"
    Eleven = "eleven"
    Twelve = "twelve"
    Thirteen = "thirteen"
    Fourteen = "fourteen"
    Fifteen = "fifteen"
    Sixteen = "sixteen"

    def __str__(self):
        return self.value
