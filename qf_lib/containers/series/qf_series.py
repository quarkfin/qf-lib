#     Copyright 2016-present CERN – European Organization for Nuclear Research
#
#     Licensed under the Apache License, Version 2.0 (the "License");
#     you may not use this file except in compliance with the License.
#     You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.

from datetime import datetime
from typing import Union, Callable

import numpy as np
import pandas as pd
from pandas.core.construction import is_empty_data

from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.time_indexed_container import TimeIndexedContainer


class QFSeries(pd.Series, TimeIndexedContainer):
    """
    Base class for all time-indexed series used in the quant-fin project.
    """

    def __init__(self, data: object = None, index: object = None, dtype: object = None, name: object = None,
                 copy: object = False, fastpath: object = False):
        if is_empty_data(data) and dtype is None:
            dtype = np.dtype(np.float64)
        super().__init__(data, index, dtype, name, copy, fastpath)

    @property
    def _constructor(self):
        return QFSeries

    @property
    def _constructor_expanddim(self):
        from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
        return QFDataFrame

    def to_log_returns(self) -> "LogReturnsSeries":
        """
        Converts timeseries to the timeseries of logarithmic returns. First date of prices in the returns timeseries
        won't be present.

        Returns
        -------
        LogReturnsSeries
            timeseries of log returns
        """
        raise NotImplementedError()

    def to_simple_returns(self) -> "SimpleReturnsSeries":
        """
        Converts timeseries to the timeseries of simple returns. First date of prices in the returns timeseries won't
        be present.

        Returns
        -------
        SimpleReturnsSeries
            timeseries of simple returns
        """
        raise NotImplementedError()

    def to_prices(self, initial_price: float = None, suggested_initial_date: Union[datetime, int, float] = None,
                  frequency: Frequency = None) -> "PricesSeries":
        """
        Converts a timeseries into series of prices. The timeseries of prices returned will have an extra date
        at the beginning (in comparison to the returns' timeseries). The difference between the extra
        date and the rest of the dates can be inferred from the returns' timeseries or can be calculated using
        the frequency passed as the optional argument. Additional date at the beginning (so called "initial date")
        is caused by the fact, that return for the first date of prices timeseries cannot be calculated, so it's
        missing. Thus, during the opposite conversion, extra date at the beginning will be added.

        Parameters
        ----------
        initial_price
            initial price of the timeseries. If no price will be specified, then it will be assumed to be 1.
        suggested_initial_date
            the first date or initial value for the prices series. It won't be necessarily the first date of the price
            series (e.g. if the method is run on the PricesSeries then it won't be used).
        frequency
            the frequency of the returns' timeseries. It is used to infer the initial date for the prices series.

        Returns
        -------
        PricesSeries
            series of prices
        """
        raise NotImplementedError()

    def min_max_normalized(self, original_min_value: float = None, original_max_value: float = None) -> "QFSeries":
        """
        Normalizes the data using min-max scaling: it maps all the data to the [0;1] range, so that 0 corresponds
        to the minimal value in the original series and 1 corresponds to the maximal value. It is also possible
        to specify values which should correspond to 0 and 1 after applying the normalization. It is useful if the same
        normalization parameters are used to normalize different data.

        Parameters
        ----------
        original_min_value
            value which should correspond to 0 after applying the normalization
        original_max_value
            value which should correspond to 1 after applying the normalization

        Returns
        -------
        normalized_series
            series of normalized values
        """
        # assert that user specified either both min and max values or none of them
        assert (original_min_value is None and original_max_value is None) or \
               (original_min_value is not None and original_max_value is not None)

        if original_min_value is None and original_max_value is None:
            original_min_value = np.nanmin(self.values)
            original_max_value = np.nanmax(self.values)

        values_span = original_max_value - original_min_value
        normalized_values = (self.values - original_min_value) / values_span

        return self._constructor(data=normalized_values, index=self.index.copy()).__finalize__(self)

    def exponential_average(self, lambda_coeff: float = 0.94) -> "QFSeries":
        """
        Calculates the exponential average of a series.

        Parameters
        ----------
        lambda_coeff
            lambda coefficient

        Returns
        -------
        QFSeries
            exponential average of the series

        """
        smoothed_series = self.copy(deep=True)

        for i in range(1, len(self)):
            current_value_weighted = lambda_coeff * self.iloc[i]
            prev_value_weighted = (1 - lambda_coeff) * smoothed_series.iloc[i - 1]

            smoothed_value = current_value_weighted + prev_value_weighted
            smoothed_series.iloc[i] = smoothed_value

        return smoothed_series

    def rolling_window_with_benchmark(self, benchmark: "QFSeries", window_size: int,
                                      func: Callable[["QFSeries"], float], step: int = 1) -> "QFSeries":
        """
        Looks at a number of windows of size ``window_size`` and transforms the data in those windows based on the
        specified ``func``.

        The window indices are stepped at a rate specified by ``step``. This function runs a "correlated"
        rolling window iteration. The ``func`` must accept two arguments, one from each series.

        Parameters
        ----------
        benchmark
            The benchmark to compare to.
        window_size
            The size of the window to look at specified as the number of data points.
        func
            The function to call during each iteration. When ``other`` is ``None`` this function should take
            two ``QFSeries`` arguments and return a value. (Usually a number such as a ``float``).
        step
            The amount of data points to step through after each iteration, i.e. how much to move the window by in
            each iteration.

        Returns
        -------
        QFSeries
            A ``QFSeries`` containing the transformed data.
        """

        result = QFSeries()

        # Intersect the two series' indexes.
        self_series = QFSeries(self)
        benchmark_series = QFSeries(benchmark)
        self_series.index = self_series.index.normalize()
        benchmark_series.index = benchmark_series.index.normalize()
        intersected = pd.concat([self_series, benchmark_series], axis=1, join="inner")
        assert isinstance(intersected, pd.DataFrame)  # Just to make PyCharm silent.

        # Apply a rolling window transformation on the QFSeries.
        # Based on https://github.com/quantopian/pyfolio/blob/master/pyfolio/timeseries.py#L616.
        window_start = 0
        while window_start + window_size < len(intersected):
            # Calculate the position of the window's end.
            window_end = window_start + window_size
            # Get the start and end dates at the current window indexes.
            start = intersected.index[window_start]
            end = intersected.index[window_end]

            # Return the data for the current window.
            strategy_slice = QFSeries(intersected.iloc[:, 0].loc[start:end])
            benchmark_slice = QFSeries(intersected.iloc[:, 1].loc[start:end])
            result[end] = func(strategy_slice, benchmark_slice)

            window_start += step

        return result

    def rolling_window(self, window_size: int, func: Callable[[Union["QFSeries", np.ndarray]], float], step: int = 1,
                       optimised: bool = False) -> "QFSeries":
        """
        Looks at a number of windows of size ``window_size`` and transforms the data in those windows based on the
        specified ``func``.

        The window indices are stepped at a rate specified by ``step``.

        Parameters
        ----------
        window_size
            The size of the window to look at specified as the number of data points.
        func
            The function to call during each iteration. When ``other`` is ``None`` this function should take one
            ``QFSeries`` and return a value (Usually a number such as a ``float``). Otherwise, this function should take
            two ``QFSeries`` arguments and return a value.
        step
            The amount of data points to step through after each iteration, i.e. how much to move the window by in
            each iteration.
        optimised
            Whether the more efficient pandas algorithm should be used for the rolling window application.
            Note: This has some limitations: The ``step`` must be 1 and ``func`` will get an ``ndarray``
            parameter which only contains values and no index.

        Returns
        -------
        QFSeries
            A ``QFSeries`` containing the transformed data.
        """
        if optimised:
            from qf_lib.containers.series.cast_series import cast_series
            assert step == 1, "Optimised rolling is only possible with a step of 1."
            uncasted_result = self.rolling(window=window_size, center=False).apply(func=func)
            return cast_series(uncasted_result, self._constructor)

        result = QFSeries()

        # Apply a rolling window transformation on the QFSeries.
        # Based on https://github.com/quantopian/pyfolio/blob/master/pyfolio/timeseries.py#L616.
        window_start = 0
        while window_start + window_size <= len(self):
            # Calculate the position of the window's end.
            window_end = window_start + window_size - 1
            # Get the start and end dates at the current window indexes.
            start = self.index[window_start]
            end = self.index[window_end]

            # Return the data for the current window.
            result[end] = func(self.loc[start:end])

            window_start += step

        return result

    def get_frequency(self) -> Frequency:
        """
        Attempts to infer the frequency of this series. The analysis uses pandas' infer_freq, as well as a heuristic
        to reduce the amount of ``Irregular`` results.

        See the implementation of the Frequency.infer_freq function for more information.
        """
        return Frequency.infer_freq(self.index)

    def total_cumulative_return(self) -> float:
        """
        Calculates the total cumulative return for the series.
        """
        raise NotImplementedError()
