from typing import List


def get_values_for_common_dates(*containers: "TimeIndexedContainer", remove_nans: bool = False)\
        -> List["TimeIndexedContainer"]:
    """
    Gets list/tuple of series/dataframes (possibly mixed) and finds the common dates for all of them. Then it returns
    corresponding series/dataframes as a list. All series and dataframes in the result list contain only values
    for common dates.

    Parameters
    ----------
    containers
        variable length list of arguments where each of the arguments is a TimeIndexedContainer
    remove_nans
        if True, then all incomplete rows will be removed from each provided container before finding common dates

    Returns
    -------
    list composed of TimeIndexedContainers containing only values for common dates
    """
    if remove_nans:
        dates_axis_number = 0
        containers = [container.dropna(axis=dates_axis_number) for container in containers]

    common_dates = containers[0].index

    for i in range(1, len(containers)):
        container = containers[i]
        common_dates = common_dates.intersection(container.index)

    return [container.loc[common_dates] for container in containers]
