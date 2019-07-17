import datetime


def iso_to_gregorian(iso_year: int, iso_week: int, iso_day: int):
    """
    Gregorian calendar date for the given ISO year, week and day.

    Taken from: http://stackoverflow.com/a/33101215/492186.

    Parameters
    ----------
    iso_year
    iso_week
        From 1 to 53.
    iso_day
        From 1 to 7.

    Returns
    -------
    date
    """
    fourth_jan = datetime.date(iso_year, 1, 4)
    _, fourth_jan_week, fourth_jan_day = fourth_jan.isocalendar()
    return fourth_jan + datetime.timedelta(days=iso_day - fourth_jan_day, weeks=iso_week - fourth_jan_week)
