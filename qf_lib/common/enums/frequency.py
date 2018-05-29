import math
from enum import Enum
from functools import total_ordering
from statistics import mode
from typing import Dict

import numpy as np
import pandas
from pandas import DatetimeIndex


@total_ordering
class Frequency(Enum):
    DAILY = 252
    WEEKLY = 52
    MONTHLY = 12
    QUARTERLY = 4
    SEMI_ANNUALLY = 2
    YEARLY = 1
    IRREGULAR = 0

    def __init__(self, occurrences_in_year):
        self.occurrences_in_year = occurrences_in_year

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @classmethod
    def from_string(cls, str_name):

        name_to_frequency = {
            'daily': Frequency.DAILY,
            'weekly': Frequency.WEEKLY,
            'monthly': Frequency.MONTHLY,
            'quarterly': Frequency.QUARTERLY,
            'semi_annually': Frequency.SEMI_ANNUALLY,
            'yearly': Frequency.YEARLY,
            "irregular": Frequency.IRREGULAR
        }

        return name_to_frequency[str_name]

    def nr_of_calendar_days(self) -> int:
        return int(math.floor(365 / self.occurrences_in_year))

    def time_delta(self) -> "RelativeDelta":
        from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta

        frequency_to_delta = {
            Frequency.DAILY: RelativeDelta(days=1),
            Frequency.WEEKLY: RelativeDelta(weeks=1),
            Frequency.MONTHLY: RelativeDelta(months=1),
            Frequency.QUARTERLY: RelativeDelta(months=3),
            Frequency.SEMI_ANNUALLY: RelativeDelta(months=6),
            Frequency.YEARLY: RelativeDelta(years=1)
        }
        return frequency_to_delta[self]

    def __str__(self):
        frequency_to_name = {
            Frequency.DAILY: "daily",
            Frequency.WEEKLY: "weekly",
            Frequency.MONTHLY: "monthly",
            Frequency.QUARTERLY: "quarterly",
            Frequency.SEMI_ANNUALLY: "semi_annually",
            Frequency.YEARLY: "yearly",
            Frequency.IRREGULAR: "irregular"
        }

        return frequency_to_name[self]

    @classmethod
    def list_members(cls):
        result = []
        for key, value in cls.__members__.items():
            result.append(str(value))
        return result

    @classmethod
    def from_pandas_freq(cls, freq):
        pandas_freq_to_frequency = {
            "D": Frequency.DAILY,
            "B": Frequency.DAILY,
            "W": Frequency.WEEKLY,
            "M": Frequency.MONTHLY,
            "Q": Frequency.QUARTERLY,
            "Q-DEC": Frequency.QUARTERLY,
            "A": Frequency.YEARLY,
            None: Frequency.IRREGULAR
        }

        return pandas_freq_to_frequency[freq]

    def to_pandas_freq(self):
        frequency_to_pandas_freq = {
            Frequency.DAILY: "D",
            Frequency.WEEKLY: "W",
            Frequency.MONTHLY: "M",
            Frequency.QUARTERLY: "Q",
            Frequency.YEARLY: "A",
            Frequency.IRREGULAR: None
        }

        return frequency_to_pandas_freq[self]

    @classmethod
    def get_lowest_freq(cls, freqs: Dict[str, "Frequency"]) -> str:
        return min(freqs, key=lambda key: freqs[key].value)

    @classmethod
    def infer_freq(cls, index: DatetimeIndex) -> "Frequency":
        result = cls.from_pandas_freq(pandas.infer_freq(index))

        if result == Frequency.IRREGULAR:
            # Attempt to infer the frequency ourselves.
            diff = index.values[1:] - index.values[0:-1]
            most_popular = mode(diff).astype(
                'timedelta64[D]') / np.timedelta64(1, 'D')
            if most_popular == 1:
                result = Frequency.DAILY
            elif 29 <= most_popular <= 31:
                result = Frequency.MONTHLY
            elif 88 <= most_popular <= 92:
                result = Frequency.QUARTERLY
            elif 360 <= most_popular <= 370:
                result = Frequency.YEARLY

        return result
