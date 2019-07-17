from enum import Enum


class DateFormat(Enum):
    """
    Class defining date formats (as strings).
    """
    ISO = "%Y-%m-%d"                        # YYYY-MM-DD
    YEAR_DOT_MONTH = "%Y.%m"                # YYYY.MM
    YEAR_DOT_MONTH_DOT_DAY = "%Y.%m.%d"     # YYYY.MM.DD
    FULL_ISO = "%Y-%m-%d %H:%M:%S.%f"       # YYYY-MM-DD HH:MM:SS.ffffff (ffffff - microseconds)
    LONG_DATE = "%d %B %Y"                  # DD Mmmm YYYY (e.g. 03 March 2017)

    def __init__(self, format_string):
        self.format_string = format_string

    def __str__(self):
        return self.value
