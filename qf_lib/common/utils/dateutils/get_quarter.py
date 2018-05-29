from datetime import datetime


def get_quarter(date: datetime) -> int:
    """
    Retrieves the quarter that the specified ``date`` is in.
    """
    return (date.month-1) // 3 + 1

