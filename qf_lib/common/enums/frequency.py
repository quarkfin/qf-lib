#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

import math
from enum import Enum
from functools import total_ordering
from statistics import mode
from typing import Dict

import numpy as np
from pandas import DatetimeIndex, infer_freq
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


@total_ordering
class Frequency(Enum):
    """
    Frequency enumeration.
    """

    MIN_1 = 98280
    """1 minute frequency"""
    MIN_5 = 1965
    """5 minutes frequency"""
    MIN_10 = 9828
    """10 minutes frequency"""
    MIN_15 = 6552
    """15 minutes frequency"""
    MIN_30 = 3276
    """30 minutes frequency"""
    MIN_60 = 1638  # 1 hour, it is assumed a day has 6.5 trading hours
    """1 hour frequency"""

    DAILY = 252
    """Daily frequency"""
    WEEKLY = 52
    """Weekly frequency"""
    MONTHLY = 12
    """Monthly frequency"""
    QUARTERLY = 4
    """Quarterly frequency"""
    SEMI_ANNUALLY = 2
    """Semi annually frequency"""
    YEARLY = 1
    """Yearly frequency"""
    IRREGULAR = 0
    """Irregular frequency"""

    def __init__(self, occurrences_in_year):
        self.occurrences_in_year = occurrences_in_year

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

    @classmethod
    def from_string(cls, str_name):

        name_to_frequency = {
            '1': Frequency.MIN_1,
            '5': Frequency.MIN_5,
            '10': Frequency.MIN_10,
            '15': Frequency.MIN_15,
            '30': Frequency.MIN_30,
            '60': Frequency.MIN_60,
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

    def time_delta(self) -> RelativeDelta:
        """Maps the enum value into corresponding RelativeDelta.

        Returns
        -------
        RelativeDelta
        """
        frequency_to_delta = {
            Frequency.MIN_1: RelativeDelta(minutes=1),
            Frequency.MIN_5: RelativeDelta(minutes=5),
            Frequency.MIN_10: RelativeDelta(minutes=10),
            Frequency.MIN_15: RelativeDelta(minutes=15),
            Frequency.MIN_30: RelativeDelta(minutes=30),
            Frequency.MIN_60: RelativeDelta(minutes=60),
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
            Frequency.MIN_1: "1",
            Frequency.MIN_5: "5",
            Frequency.MIN_10: "10",
            Frequency.MIN_15: "15",
            Frequency.MIN_30: "30",
            Frequency.MIN_60: "60",
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
            "T": Frequency.MIN_1,
            "5T": Frequency.MIN_5,
            "10T": Frequency.MIN_10,
            "15T": Frequency.MIN_15,
            "30T": Frequency.MIN_30,
            "60T": Frequency.MIN_60,
            "H": Frequency.MIN_60,
            "D": Frequency.DAILY,
            "B": Frequency.DAILY,
            "W": Frequency.WEEKLY,
            "M": Frequency.MONTHLY,
            "Q": Frequency.QUARTERLY,
            "Q-DEC": Frequency.QUARTERLY,
            "A": Frequency.YEARLY,
            "Y": Frequency.YEARLY,
            None: Frequency.IRREGULAR
        }

        return pandas_freq_to_frequency[freq]

    def to_pandas_freq(self):
        frequency_to_pandas_freq = {
            Frequency.MIN_1: "T",
            Frequency.MIN_5: "5T",
            Frequency.MIN_10: "10T",
            Frequency.MIN_15: "15T",
            Frequency.MIN_30: "30T",
            Frequency.MIN_60: "60T",
            Frequency.DAILY: "D",
            Frequency.WEEKLY: "W",
            Frequency.MONTHLY: "M",
            Frequency.QUARTERLY: "Q",
            Frequency.YEARLY: "A",
            Frequency.IRREGULAR: None
        }

        try:
            return frequency_to_pandas_freq[self]
        except KeyError:
            return "{}T".format(self)

    @classmethod
    def get_lowest_freq(cls, freqs: Dict[str, "Frequency"]) -> str:
        return min(freqs, key=lambda key: freqs[key].value)

    @classmethod
    def infer_freq(cls, index: DatetimeIndex) -> "Frequency":
        result = cls.from_pandas_freq(infer_freq(index))

        if result == Frequency.IRREGULAR:
            # Attempt to infer the frequency ourselves.
            diff = index.values[1:] - index.values[0:-1]
            most_popular = mode(diff).astype(
                'timedelta64[D]') / np.timedelta64(1, 'D')
            if most_popular < 1:
                # Infer intraday frequency (change to minutes)
                most_popular = mode(diff).astype(
                    'timedelta64[m]') / np.timedelta64(1, 'm')
                if most_popular == 1:
                    result = Frequency.MIN_1
                elif 4 <= most_popular <= 6:
                    result = Frequency.MIN_5
                elif 9 <= most_popular <= 11:
                    result = Frequency.MIN_10
                elif 14 <= most_popular <= 16:
                    result = Frequency.MIN_15
                elif 29 <= most_popular <= 31:
                    result = Frequency.MIN_30
                elif 50 <= most_popular <= 70:
                    result = Frequency.MIN_60
            elif most_popular == 1:
                result = Frequency.DAILY
            elif 29 <= most_popular <= 31:
                result = Frequency.MONTHLY
            elif 88 <= most_popular <= 92:
                result = Frequency.QUARTERLY
            elif 360 <= most_popular <= 370:
                result = Frequency.YEARLY

        return result
