from typing import Union

import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.drawdown_tms import drawdown_tms
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries


def max_drawdown(input_data: Union[QFSeries, QFDataFrame], frequency: Frequency=None) -> Union[float, pd.Series]:
    """
    Finds maximal drawdown for the given timeseries of prices.

    Parameters
    ----------
    input_data
        timeseries of prices/returns
    frequency
        optional parameter that improves teh performance of the function it is not need to infer the frequency

    Returns
    -------
    max_drawdown
        maximal drawdown for the given timeseries of prices expressed as the percentage value (e.g. 0.5 corresponds
        to the 50% drawdown)
    """
    return drawdown_tms(input_data, frequency=frequency).max()
