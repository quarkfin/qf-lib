from datetime import datetime
from typing import Tuple

import pandas as pd


def get_common_start_and_end(*containers: "TimeIndexedContainer") -> Tuple[datetime, datetime]:
    """
    Finds the firt and last valid dates (with a value different than NaN) for each column and then returns the latest
    of starting dates and the soonest ending date.

    If one of containers is dataframe then it is split into separate columns first.

    Parameters
    ----------
    containers
        list of containers for which the common beginning and ending should be found

    Returns
    -------
    common_start
        soonest date on which data for all series is already available
    common_end
        latest date on which data for all series is still available
    """
    start_dates = []
    end_dates = []
    for container in containers:
        if isinstance(container, pd.DataFrame):
            start_date = container.apply(lambda col: col.first_valid_index()).max()
            start_dates.append(start_date)

            end_date = container.apply(lambda col: col.last_valid_index()).min()
            end_dates.append(end_date)
        else:
            start_dates.append(container.first_valid_index())
            end_dates.append(container.last_valid_index())

    common_start = max(start_dates)
    common_end = min(end_dates)

    return common_start, common_end
