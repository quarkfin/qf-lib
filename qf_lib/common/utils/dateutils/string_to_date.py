import datetime

from qf_lib.common.utils.dateutils.date_format import DateFormat


def str_to_date(string_date: str, date_format: DateFormat=DateFormat.ISO) -> datetime.datetime:
    """
    Converts string into date object.

    Parameters
    ----------
    string_date
        date encoded in the string
    date_format
        format of the date passed as a string

    Returns
    -------
    date
        object representing date
    """

    return datetime.datetime.strptime(string_date, date_format.value)
