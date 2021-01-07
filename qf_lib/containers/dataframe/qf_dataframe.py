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
from typing import Sized, Sequence, Callable, Union, Mapping, Dict

import numpy as np
import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.time_indexed_container import TimeIndexedContainer


class QFDataFrame(pd.DataFrame, TimeIndexedContainer):
    """
    Base class for all data frames (2-D matrix-like objects) used in the project. All the columns within
    the dataframe contain values for the same date range and have the same frequencies. All the columns are
    of the same types (e.g. log-returns/prices).
    """

    def __init__(self, data=None, index=None, columns=None, dtype=None, copy=False):
        super().__init__(data, index, columns, dtype, copy)

    @property
    def _constructor_sliced(self):
        from qf_lib.containers.series.qf_series import QFSeries
        return QFSeries

    @property
    def _constructor(self):
        return QFDataFrame

    @property
    def num_of_columns(self):
        return len(self.columns)

    @property
    def num_of_rows(self):
        return len(self.index)

    def to_log_returns(self) -> "LogReturnsDataFrame":
        """
        Converts dataframe to the dataframe of logarithmic returns. First date of prices in the returns dataframe
        won't be present.

        Returns
        -------
        LogReturnsDataFrame
            dataframe of log returns
        """
        from qf_lib.containers.dataframe.log_returns_dataframe import LogReturnsDataFrame

        series_type = self._constructor_sliced
        dataframe = self.apply(series_type.to_log_returns, axis=0)
        dataframe = cast_dataframe(dataframe, LogReturnsDataFrame)

        return dataframe

    def to_simple_returns(self) -> "SimpleReturnsDataFrame":
        """
        Converts dataframe to the dataframe of simple returns. First date of prices in the returns timeseries won't
        be present.

        Returns
        -------
        SimpleReturnsDataFrame
            dataframe of simple returns
        """
        from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame

        series_type = self._constructor_sliced
        dataframe = self.apply(series_type.to_simple_returns, axis=0)
        dataframe = cast_dataframe(dataframe, SimpleReturnsDataFrame)

        return dataframe

    def to_prices(self, initial_prices: Sequence[float] = None,
                  suggested_initial_date: Union[datetime, int, float] = None,
                  frequency: Frequency = None) -> "PricesDataFrame":
        """
        Converts a dataframe to the dataframe of prices. The dataframe of prices returned will have an extra date
        at the beginning (in comparison to the returns' dataframe). The difference between the extra
        date and the rest of the dates can be inferred from the returns' dataframe or can be calculated using
        the frequency passed as the optional argument. Additional date at the beginning (so called "initial date")
        is caused by the fact, that return for the first date of prices timeseries cannot be calculated, so it's
        missing. Thus, during the opposite conversion, extra date at the beginning will be added.

        Parameters
        ----------
        initial_prices
            initial price for all timeseries. If no prices are specified, then they will be assumed to be 1. If only one
            value is passed (instead of a list with values for each column), then the initial price will be the same
            for each series contained within the dataframe.
        suggested_initial_date
            the first date or initial value for the prices series. It won't be necessarily the first date of the price
            series (e.g. if the method is run on the PricesDataFrame then it won't be used).
        frequency
            the frequency of the returns' timeseries. It is used to infer the initial date for the prices series.

        Returns
        -------
        PricesDataFrame
            dataframe of prices
        """
        initial_prices = self._prepare_value_per_column_list(initial_prices)

        initial_prices_iter = self._get_iterator_for_pandas(initial_prices)

        def to_prices_func(series, init_prices_iter=initial_prices_iter,
                           suggested_init_date=suggested_initial_date, freq=frequency):
            initial_price = next(init_prices_iter)
            prices_series = series.to_prices(initial_price=initial_price, suggested_initial_date=suggested_init_date,
                                             frequency=freq)
            return prices_series

        dataframe = self.apply(to_prices_func, axis=0)

        from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
        dataframe = cast_dataframe(dataframe, PricesDataFrame)
        return dataframe

    def min_max_normalized(self, original_min_values: Sequence[float] = None,
                           original_max_values: Sequence[float] = None) -> "QFDataFrame":
        """
        Normalizes the data using min-max scaling: it maps all the data to the [0;1] range, so that 0 corresponds
        to the minimal value in the original series and 1 corresponds to the maximal value. It is also possible
        to specify values which should correspond to 0 and 1 after applying the normalization. It is useful if the same
        normalization parameters are used to normalize different data.

        Parameters
        ----------
        original_min_values
            values which should correspond to 0 after applying the normalization (one value for each column)
        original_max_values
            values which should correspond to 1 after applying the normalization (one value for each column)

        Returns
        -------
        QFDataFrame
            dataframe of normalized values
        """
        # assert that user specified either both min and max values or none of them
        min_values = self._prepare_value_per_column_list(original_min_values)
        max_values = self._prepare_value_per_column_list(original_max_values)

        min_values_iter = self._get_iterator_for_pandas(min_values)
        max_values_iter = self._get_iterator_for_pandas(max_values)

        def min_max_norm_func(column, min_val_iter=min_values_iter, max_val_iter=max_values_iter):
            norm_column = column.min_max_normalized(next(min_val_iter), next(max_val_iter))
            return norm_column

        norm_dataframe = self.apply(min_max_norm_func, axis=0)
        norm_dataframe = cast_dataframe(norm_dataframe, self._constructor)
        return norm_dataframe

    def exponential_average(self, lambda_coeff: float = 0.94) -> "QFDataFrame":
        """
        Calculates the exponential average of a dataframe.

        Parameters
        ----------
        lambda_coeff
            lambda coefficient

        Returns
        -------
        QFDataFrame
            smoothed version (exponential average) of the data frame

        """
        lambda_coefficients = self._prepare_value_per_column_list(lambda_coeff)
        lambda_coefficients_iter = self._get_iterator_for_pandas(lambda_coefficients)

        def exponential_avg_func(column, lambda_coeff_iter=lambda_coefficients_iter):
            lambda_coefficient = next(lambda_coeff_iter)
            smoothed_column = column.exponential_average(lambda_coefficient)
            return smoothed_column

        smoothed_df = self.apply(exponential_avg_func, axis=0)
        smoothed_df = cast_dataframe(smoothed_df, self._constructor)
        return smoothed_df

    def total_cumulative_return(self) -> "QFSeries":
        """
        Calculates total cumulative return for each column.

        Returns
        -------
        QFSeries
            Series containing total cumulative return for each column of the original DataFrame.
        """
        series_type = self._constructor_sliced
        series = self.apply(series_type.total_cumulative_return, axis=0)
        series = cast_series(series, series_type)

        return series

    def _prepare_value_per_column_list(self, values):
        if isinstance(values, Sized):
            self._assert_is_valid_values_list(values)
            result_values = values
        else:
            result_values = [values] * self.num_of_columns

        return result_values

    def _get_iterator_for_pandas(self, result_values):
        """
        Creates iterator suitable to be used with pandas.apply function.
        As since pandas 1.1.0 apply and applymap on DataFrame evaluates first row/column only once there is no need to
        iterate over the first element twice in the generator.
        """
        if isinstance(result_values, np.ndarray):
            result_values = result_values.tolist()

        return iter(result_values)

    def _assert_is_valid_values_list(self, values):
        num_of_values = len(values)
        if num_of_values != self.num_of_columns:
            error_msg = "Number of elements in the list must be equal to number of columns " \
                        "(is: {0}, should be: {1}".format(num_of_values, self.num_of_columns)
            raise ValueError(error_msg)

    def rolling_window(self, window_size: int, func: Callable[[Union["QFSeries", np.ndarray]], float], step: int = 1,
                       optimised: bool = False) -> "QFDataFrame":
        """
        Looks at a number of windows of size ``window_size`` and transforms the data in those windows based on the
        specified ``func``. This is performed for each column inside this data frame.

        The window indices are stepped at a rate specified by ``step``.

        **Warning**: The ``other`` parameter is only present to keep consistency with QFSeries' rolling_window
        function, it should always be ``None``.

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
        QFDataFrame
            data frame containing the transformed data
        """
        if optimised:
            assert step == 1, "Optimised rolling is only possible with a step of 1."
            return self.rolling(window=window_size, center=False).apply(func=func)

        result = QFDataFrame()
        for col in self:
            transformed_data = self[col].rolling_window(window_size, func, step=step)
            result[col] = transformed_data
        return result

    def rolling_time_window(
            self, window_length: int, step: int, func: Callable[[Union["QFDataFrame", np.ndarray]], "QFSeries"]) \
            -> Union[None, "QFSeries", "QFDataFrame"]:
        """
        Runs a given function on each rolling window in the dataframe. The content of a rolling window is also
        a QFDataFrame thus the funciton which should be applied should accept a QFDataFrame as an argument.

        The function may return either a QFSeries (then the output of rolling_time_window will be QFDataFrame)
        or a scalar value (then the output of rolling_time_window will be QFSeries).

        The rolling window is moved along the time index (rows).

        Parameters
        ----------
        window_length
            number of rows which should be taken into rolling window
        step
            number of rows by which rolling window should be moved
        func
            function to apply on each rolling window. If it returns a QFSeries then the output of rolling_time_window()
            will be a QFDataFrame; if it returns a scalar value, the return value of rolling_time_window() will
            be a QFSeries

        Returns
        -------
        None, QFSeries, QFDataFrame
            None (if the result of running the rolling window was empty) or QFSeries (if the function applied returned
            scalar value for each window) or QFDataFrame (if the function applied returned QFSeries for each window)
        """
        results_dict = dict()  # type: Dict[datetime, pd.Series]
        end_idx = self.num_of_rows

        while True:
            start_idx = end_idx - window_length
            if start_idx < 0:
                break

            patch = self.iloc[start_idx:end_idx, :]
            end_date = self.index[end_idx - 1]
            results_dict[end_date] = func(patch)

            end_idx -= step

        if not results_dict:
            return None

        first_element = next(iter(results_dict.values()))  # type: "QFSeries"

        if isinstance(first_element, pd.Series):
            result = QFDataFrame.from_dict(results_dict, orient='index')
            result = cast_dataframe(result, QFDataFrame)
        else:
            from qf_lib.containers.series.qf_series import QFSeries
            dates_and_values = [(date, value) for date, value in results_dict.items()]
            dates, values = zip(*dates_and_values)
            result = QFSeries(index=dates, data=values)

        result = result.sort_index()
        return result

    def get_frequency(self) -> Mapping[str, Frequency]:
        """
        Attempts to infer the frequency of each column in this dataframe. The analysis uses pandas' infer_freq,
        as well as a heuristic to reduce the amount of ``Irregular`` results.

        See the implementation of the Frequency.infer_freq function for more information.
        """
        result = {}
        for col in self:
            series = self[col]
            if not series.isnull().all():
                # Drop NaN rows only when the series has at least one non-NaN value.
                # This is necessary because the series has been packed with other series which might have a higher
                # frequency.
                series = series.dropna(axis=0)

            result[col] = Frequency.infer_freq(series.index)
        return result
