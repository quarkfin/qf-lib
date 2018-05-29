from qf_lib.common.enums.frequency import Frequency


def get_grouping_for_frequency(frequency):
    """
    Returns a proper grouping function which can then be applied in the series.groupby() or dataframe.groupby().
    """
    if frequency == Frequency.DAILY:
        grouping = [lambda x: x.day, lambda x: x.month, lambda x: x.year]
    elif frequency == Frequency.WEEKLY:
        grouping = [lambda x: x.year, lambda x: x.week]
    elif frequency == Frequency.MONTHLY:
        grouping = [lambda x: x.year, lambda x: x.month]
    elif frequency == Frequency.YEARLY:
        grouping = [lambda x: x.year]
    else:
        raise ValueError('convert_to must be {}, {}, {} or {}'.format(Frequency.DAILY, Frequency.WEEKLY,
                                                                      Frequency.MONTHLY, Frequency.YEARLY))
    return grouping
