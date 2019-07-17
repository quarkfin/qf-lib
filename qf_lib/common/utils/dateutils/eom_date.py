import calendar
import datetime


def eom_date(date: datetime.datetime = None, year: int = None, month: int = None) -> datetime.datetime:
    """
    Tells what is the last date of the month for given date or for given year and a month.

    Parameters
    ----------
    date
        date for which the corresponding last date of the month should be returned
    year
        year containing the month for which last date of the month should be returned
    month
        number of month (1 -> January, 2-> February, ...) for which the last date of the month will be returned

    Returns
    -------

    """
    if date is not None:
        assert year is None and month is None
        year = date.year
        month = date.month
    else:
        assert year is not None and month is not None

    weekday, last_day_in_month = calendar.monthrange(year, month)
    return datetime.datetime(year, month, last_day_in_month)
