from datetime import datetime

from qf_lib.common.enums.frequency import Frequency


def get_grouping_for_frequency(frequency):
    """
    Returns a proper grouping function which can then be applied in the series.groupby() or dataframe.groupby().
    """
    if frequency == Frequency.DAILY:
        grouping = [lambda x: x.day, lambda x: x.month, lambda x: x.year]
    elif frequency == Frequency.WEEKLY:
        # by ISO standards first week of the year is the first one that contains Thursday. Each ISO week starts with
        # Monday. E.g. 2014-12-29 (Monday) is the first day of the first week in 2015, because Thursday of that week
        # belongs to the 2015 (it's 2015-01-01).
        grouping = [lambda x:  datetime(x.year, x.month, x.day).isocalendar()[:2]]
    elif frequency == Frequency.MONTHLY:
        grouping = [lambda x: x.year, lambda x: x.month]
    elif frequency == Frequency.YEARLY:
        grouping = [lambda x: x.year]
    else:
        raise ValueError('convert_to must be {}, {}, {} or {}'.format(Frequency.DAILY, Frequency.WEEKLY,
                                                                      Frequency.MONTHLY, Frequency.YEARLY))
    return grouping
