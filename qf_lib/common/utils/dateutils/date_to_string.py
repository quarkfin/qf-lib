import datetime

from qf_lib.common.utils.dateutils.date_format import DateFormat


def date_to_str(date: datetime.datetime, date_format: DateFormat=DateFormat.ISO) -> str:
    """
    Converts date object into string.

    Parameters
    ----------
    date
        date to be converted to string
    date_format
        date format of the output string

    Returns
    -------
    string representation of a given date
    """

    return date.strftime(date_format.format_string)
