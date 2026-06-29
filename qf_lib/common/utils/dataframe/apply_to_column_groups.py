from typing import Callable, Hashable

import pandas as pd


def apply_to_column_groups(
    frame: pd.DataFrame, by: Callable[[Hashable], Hashable], func: Callable[[pd.DataFrame], pd.Series]
) -> pd.DataFrame:
    grouped = frame.T.groupby(by)
    return grouped.apply(lambda group: func(group.T)).T
