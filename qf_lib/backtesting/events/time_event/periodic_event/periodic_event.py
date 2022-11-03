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

from abc import abstractmethod, ABCMeta
from datetime import datetime
from typing import Dict, List

from qf_lib.backtesting.events.time_event.regular_date_time_rule import RegularDateTimeRule
from qf_lib.backtesting.events.time_event.regular_time_event.regular_time_event import RegularTimeEvent
from qf_lib.backtesting.events.time_event.time_event import TimeEvent
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class PeriodicEvent(TimeEvent, metaclass=ABCMeta):
    """
    TimeEvent which is triggered every certain amount of time (given a certain frequency) within a predefined time
    range.

    As some of the available frequencies (like e.g. Frequency.MIN_15) can not be implemented using only one
    RegularTimeEvent, the PeriodicEvent contains a list of multiple custom RegularTimeEvents (_events_list).
    Each of these RegularTimeEvents contains its own _trigger_time_rule. These rules are used to define the desired
    frequency of PeriodicEvent.

    E.g. PeriodicEvent, which has the frequency parameter set to Frequency.MIN_15 is further translated to a list
    of multiple RegularTimeEvents, which correspond to RegularDateTimeRules with following trigger time parameters:

    {"minute": 0, "second": 0, "microsecond": 0} - event triggered at every full hour, eg. 12:00, 13:00 etc.
    {"minute": 15, "second": 0, "microsecond": 0} - event triggered at 12:15, 13:15 etc.
    {"minute": 30, "second": 0, "microsecond": 0} - event triggered at 12:30, 13:30 etc.
    {"minute": 45, "second": 0, "microsecond": 0} - event triggered at 12:45, 13:45 etc.

    All the above defined Events together, create an Event which is triggered every 15 minutes.

    The PeriodicEvent is triggered only within the [start_time, end_time] time range with the given frequency.
    It is triggered always at the start_time, but not necessarily at the end_time.
    E.g.
        start_time = {"hour": 13, "minute": 20, "second": 0, "microsecond": 0},
        end_time = {"hour": 16, "minute": 0, "second": 0, "microsecond": 0},
        frequency = Frequency.MIN_30

        This event will be triggered at 13:20, 13:50, 14:20, 14:50, 15:20, 15:50, but not at 16:00.

    Both start_time and end_time dictionaries should contain "hour", "minute", "second" and "microsecond" fields.
    """

    start_time = None  # type: Dict[str, int] # {"hour": 13, "minute": 20, "second": 0, "microsecond": 0}
    end_time = None  # type: Dict[str, int]  # {"hour": 20, "minute": 0, "second": 0, "microsecond": 0}
    frequency = None  # type: Frequency
    _events_list = None  # List[RegularTimeEvent]

    _run_over_weekends: bool = True

    def __init__(self):
        if None in (self.start_time, self.end_time):
            raise ValueError("set up the start and end time by calling set_start_and_end_time() before using the event")

        if self.frequency is None:
            raise ValueError("set up the frequency by calling set_frequency() before using the event")

        self._init_events_list()

    @classmethod
    def set_start_and_end_time(cls, start_time: Dict[str, int], end_time: Dict[str, int]):
        zeroed_seconds_dict = {"second": 0, "microsecond": 0}
        cls.start_time = start_time.copy()
        cls.start_time.update(zeroed_seconds_dict)

        cls.end_time = end_time.copy()
        cls.end_time.update(zeroed_seconds_dict)

    @classmethod
    def set_frequency(cls, frequency: Frequency):
        cls.frequency = frequency

    def _init_events_list(self):
        """
        Updates the _events_list - list consisting of custom RegularTimeEvents (PeriodicRegularEvent), which are used to
        compute the next trigger time of PeriodicEvent. The notify function of PeriodicRegularEvent is empty, as it is
        not currently used - the purpose of defining the PeriodicRegularEvents is to easily obtain the next trigger
        time and then notify the listener attached to the PeriodicEvent.
        """
        self._events_list = []
        # Generate the list of time dictionaries
        _trigger_time_list = self._frequency_to_trigger_time()

        for _trigger_time in _trigger_time_list:
            # Define a custom regular time event
            self._events_list.append(self._PeriodicRegularEvent(
                trigger_time=_trigger_time,
                start_time=self.start_time,
                end_time=self.end_time,
                run_on_weekends=self._run_over_weekends
            ))

    class _PeriodicRegularEvent(RegularTimeEvent):

        _trigger_time = None

        def __init__(self, trigger_time, start_time, end_time, run_on_weekends: bool):
            self._trigger_time = trigger_time
            self._start_time = start_time
            self._end_time = end_time
            self._trigger_time_rule = RegularDateTimeRule(**trigger_time)
            self._run_on_weekends = run_on_weekends

        @classmethod
        def trigger_time(cls) -> RelativeDelta:
            return RelativeDelta(**cls._trigger_time)

        def next_trigger_time(self, now: datetime) -> datetime:

            def _within_time_frame(_time):
                return (_time + RelativeDelta(**self._end_time) >= _time) and \
                       (_time + RelativeDelta(**self._start_time) <= _time)

            _start_time_rule = RegularDateTimeRule(**self._start_time)

            # Before midnight and after end time or after midnight and before start time (e.g. after the market
            # close and before the market open), the next trigger time should always point to the next time
            # triggered by the _start_time_rule (e.g. to the market open time)
            if not _within_time_frame(now):
                _next_trigger_time = _start_time_rule.next_trigger_time(now)
            else:
                _next_trigger_time = self._trigger_time_rule.next_trigger_time(now)
                # If the next trigger time is outside the desired time frame, find the next event time moving
                # current time to the next start_time date.
                if not _within_time_frame(_next_trigger_time):
                    _next_trigger_time = _start_time_rule.next_trigger_time(_next_trigger_time)

            if not self._run_on_weekends and _next_trigger_time.weekday() in (5, 6):
                # recursive call to get the next valid trigger time
                _next_trigger_time = self.next_trigger_time(_next_trigger_time)

            return _next_trigger_time

        def notify(self, listener) -> None:
            pass

    def next_trigger_time(self, now: datetime) -> datetime:
        # List of times triggered by any of the constituent of the PeriodicEvent. The next trigger time of PeriodicEvent
        # is the first of the times listed in next_trigger_times list.
        next_trigger_times = [event.next_trigger_time(now) for event in self._events_list]
        return min(next_trigger_times)

    @abstractmethod
    def notify(self, listener) -> None:
        pass

    def _frequency_to_trigger_time(self) -> List[Dict]:
        """
        Helper function, which creates a list of regular time dictionaries, which are compliant with the certain
        given self.frequency and shifted according to the self.start_time.

        E.g. in case of frequency equal to 30 minutes and zeroed self.start_time = {"minute": 0, "second": 0}
        the function will create the following list of dictionaries:
        [{"minute": 0, "second": 0, "microsecond": 0},
        {"minute": 30, "second": 0, "microsecond": 0}].

        In case of 15 minutes frequency and self.start_time = {"minute": 20, "second": 0} the output will
        be as follows:
        [{"minute": 20, "second": 0, "microsecond": 0},
        {"minute": 35, "second": 0, "microsecond": 0},
        {"minute": 55, "second": 0, "microsecond": 0},
        {"minute": 5, "second": 0, "microsecond": 0}].

        Two most important parameters used as a base for generating the trigger time dictionaries are self.frequency
        and the self.start_time.

        self.start_time - this dictionary contains e.g. minute, second fields, which denote the shift which should be
        applied to the returned values. It is necessary to provide the values of self.start_time to align the returned
        values to the start time (e.g. market open time). If the market open time opens at 9:30, then without shifting
        the data, the returned list will be as follows: [{"minute": 0, "second": 0, "microsecond": 0}]. If we will use
        this dictionary as the base for time triggering, the events will be triggered at 10:00, 11:00 etc.
        After providing the self.start_time  shift equal to {"minute": 30"}, it will be possible to trigger events at
        9:30, 10:30, etc.
        """

        # Helper dictionary consisting of number of minutes per hour, months per year, etc. used to compute the time
        # shift for a given frequency
        max_time_values = {
            "microsecond": 1000000,
            "second": 60,
            "minute": 60,
            "hour": 24,
            "weekday": 7,
            "month": 12,
        }

        def _generate_time_dict(slice_field: str, slice_field_value: int, shift: Dict) -> Dict:
            """
            Generate a single time dictionary, e.g. {"minute": 13, "second": 0, "microsecond": 0}

            Parameters:
            ===========
            slice_field
                The first meaningful time parameter, which will appear in the created time dictionary. E.g. in case of
                minutely frequency, we would like to receive {"second": 0, "microsecond": 0} as function output, as this
                dictionary may be used to trigger events for every minute, when seconds and microseconds part are equal to
                0. Thus, in case of 1 minute frequency, slice_field, the first meaningful time field is "second".
            slice_field_value
                The value, which should appear in the final dictionary for the given slice_field, e.g. {"second": 14}. This
                value may be changed in final dictionary, to align with the provided shift parameter.
            shift
                Time dictionary, denoting values of time shift, that should be applied for each time parameter ("hour",
                "minute" etc.). E.g. In case of slice_field = "minute", slice_field_value = 45 and shift = {"minute": 20}
                the following dictionary will be returned:
                {"minute": 5, "second": 0, "microsecond": 0}.
            """
            # All fields that may appear in the output dictionary
            fields = ("year", "month", "day", "weekday", "hour", "minute", "second", "microsecond")

            # Create dictionary from consecutive fields, starting from the first most meaningful - slice_field. Set all
            # values to 0, except of the dictionary[slice_field], which should be set to the desired slice_field_value.
            slice_index = fields.index(slice_field)
            time_dict = dict.fromkeys(fields[slice_index:], 0)
            time_dict[slice_field] = slice_field_value

            # Shift the values according to the shift dictionary - the resulting dictionary should contain all these
            # fields, which appear in time_dict. As some of the keys may appear in both dictionaries,
            # e.g. time_dict["minute"] = 20, shift["minute"] = 30, we have to sum them to receive
            # time_dict["minute"] = 50.

            # In order to prevent this sum from exceeding the maximum values, we additionally use modulo function with
            # the maximum value given by the max_time_values dictionary.
            # E.g. time_dict["minute"] = 40, shift["minute"] = 40,
            # time_dict["minute"] = 80 % max_time_values["minute"] = 20

            result = {
                key: (time_dict.get(key, 0) + shift.get(key, 0)) % max_time_values[key]
                for key in time_dict.keys()
            }

            return result

        # Dictionary containing the first meaningful time parameters and their corresponding values for each frequency
        # The fields values are used to compute the frequency
        frequency_to_time_dict = {
            Frequency.MIN_1: ("second", 0),
            Frequency.MIN_5: ("minute", 5),
            Frequency.MIN_10: ("minute", 10),
            Frequency.MIN_15: ("minute", 15),
            Frequency.MIN_30: ("minute", 30),
            Frequency.MIN_60: ("minute", 0),
            Frequency.DAILY: ("hour", 0),
            Frequency.WEEKLY: ("weekday", 0),
            Frequency.MONTHLY: ("day", 0),
            Frequency.QUARTERLY: ("month", 3),
            Frequency.SEMI_ANNUALLY: ("month", 6),
            Frequency.YEARLY: ("month", 0)
        }

        # Get the first meaningful field and the field value
        field, time_freq = frequency_to_time_dict[self.frequency]
        # Create a range of field_values (e.g. in case of 15 minutes frequency: (0, 15, 30, 45)
        freq_range = range(0, max_time_values[field], time_freq) if time_freq > 0 else (0,)
        # Create a list of time dictionaries for each field and its value, given by the freq_range
        time_dictionaries = [_generate_time_dict(field, field_value, self.start_time) for field_value in freq_range]
        return time_dictionaries

    @classmethod
    def exclude_weekends(cls):
        """
        If called, the periodic event will not be notified over the weekends.
        Initiation of PeriodicEvent must be after setting the exclude_weekends because of the
        PeriodicEvnet _events_list attribute
        """
        cls._run_over_weekends = False
