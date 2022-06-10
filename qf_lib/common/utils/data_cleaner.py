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

from qf_lib.common.utils.dateutils.get_values_common_dates import get_values_for_common_dates
from qf_lib.common.utils.returns.beta_and_alpha import beta_and_alpha
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.cast_series import cast_series
from qf_lib.containers.series.qf_series import QFSeries


class DataCleaner:
    """
    Cleans data which is partially incomplete, e.g. has gaps

    Parameters
    ----------
    dataframe: SimpleReturnsDataFrame
        DataFrame of simple returns. If one column has more missing values than the threshold, it is removed
        from the result.
    threshold: float
        top limit of missing data. If the amount of missing data in a series exceeds this limit, the series will be
        removed. It is a relative value (e.g. 0.02, which corresponds to 2% of the data from the series).
    """
    def __init__(self, dataframe: SimpleReturnsDataFrame, threshold: float = 0.05):
        assert isinstance(dataframe, SimpleReturnsDataFrame)
        self.dataframe = dataframe
        self.threshold = threshold
        self.incorrect_columns = []  # Columns which contain only NaN values.
        self.start_late_columns = {}  # Columns which start late together with their start date.
        self.columns_with_holes = []  # Columns which have one or more NaN values in them.

    def proxy_using_value(self, proxy_value: float) -> SimpleReturnsDataFrame:
        """
        Removes columns from the DataFrame which have too many missing values. Then, the missing data in the remaining
        columns is completed using a given proxy_value.

        Parameters
        ----------
        proxy_value: float
            value with which all the missing data should be filled

        Returns
        -------
        SimpleReturnsDataFrame
            completed dataframe without missing data
        """
        result_dataframe = self.dataframe.copy(deep=True)
        empty_values_idx = self.dataframe.isnull()

        self._drop_underfilled_columns(result_dataframe, empty_values_idx)
        result_dataframe[empty_values_idx] = proxy_value

        return result_dataframe

    def proxy_using_regression(self, benchmark_tms: QFSeries, columns_type: type) -> SimpleReturnsDataFrame:
        """
        Removes columns from the DataFrame which have too many missing values. Then, the missing data in the remaining
        columns is completed using regression with the benchmark.

        Parameters
        ----------
        benchmark_tms: QFSeries
            benchmark used indirectly to proxy the missing data in the Dataframe.
        columns_type: type
            type of each column (e.g. PricesSeries, LogReturnsSeries)

        Returns
        -------
        SimpleReturnsDataFrame
            completed dataframe. However it can still contain missing data, because sometimes it is not possible to
            complete all data using regression (e.g. for data that is missing in the original series there is
            no corresponding benchmark value).
        """
        result_dataframe = self.dataframe.copy(deep=True)
        empty_values_idx = self.dataframe.isnull()

        self._drop_underfilled_columns(result_dataframe, empty_values_idx)
        self._use_regression_to_fill_missing_data(
            benchmark_tms, columns_type, result_dataframe, empty_values_idx)

        return result_dataframe

    def _drop_underfilled_columns(self, result_dataframe, empty_values_idx):
        columns_to_delete = []
        for column_name, is_empty_values in empty_values_idx.iteritems():
            empty_values_ratio = sum(is_empty_values) / len(is_empty_values)  # #empty_values / #all_values

            if empty_values_ratio > self.threshold:
                columns_to_delete.append(column_name)

                first_valid_index = self.dataframe[column_name].first_valid_index()
                if empty_values_ratio == 1:
                    self.incorrect_columns.append(column_name)
                elif self.dataframe[column_name][first_valid_index:].isnull().any():
                    self.columns_with_holes.append(column_name)
                elif first_valid_index != self.dataframe[column_name].index[0]:
                    self.start_late_columns[column_name] = first_valid_index
                else:
                    assert False, "Unknown reason for dropping column " + column_name

        empty_values_idx.drop(columns_to_delete, axis=1, inplace=True)
        result_dataframe.drop(columns_to_delete, axis=1, inplace=True)

    def _use_regression_to_fill_missing_data(self, benchmark_tms, columns_type, result_dataframe, empty_values_idx):
        num_of_columns = result_dataframe.shape[1]
        for i in range(num_of_columns):
            column = result_dataframe.iloc[:, i]
            nans_in_column_idx = empty_values_idx.iloc[:, i]
            beta, alpha = self._get_beta_and_alpha(
                benchmark_tms, column, columns_type, nans_in_column_idx)

            benchmark_common_tms, nans_common_idx = get_values_for_common_dates(
                benchmark_tms, nans_in_column_idx)
            benchmark_values_for_missing_dates = benchmark_common_tms[nans_common_idx]
            missing_values = beta * benchmark_values_for_missing_dates + alpha
            column[nans_in_column_idx] = missing_values

        return result_dataframe

    def _get_beta_and_alpha(self, benchmark_tms, column, columns_type, nans_in_column_idx):
        column_without_nans = column[~nans_in_column_idx]
        column_without_nans = cast_series(column_without_nans, columns_type)
        beta, alpha = beta_and_alpha(column_without_nans, benchmark_tms)
        return beta, alpha
