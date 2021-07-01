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

from typing import List, Tuple, Sequence, Union

from qf_lib.analysis.timeseries_analysis.timeseries_analysis_dto import TimeseriesAnalysisDTO
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.miscellaneous.annualise_with_sqrt import annualise_with_sqrt
from qf_lib.common.utils.miscellaneous.kelly import kelly
from qf_lib.common.utils.ratios.calmar_ratio import calmar_ratio
from qf_lib.common.utils.ratios.gain_to_pain_ratio import gain_to_pain_ratio
from qf_lib.common.utils.ratios.omega_ratio import omega_ratio
from qf_lib.common.utils.ratios.sharpe_ratio import sharpe_ratio
from qf_lib.common.utils.ratios.sorino_ratio import sorino_ratio
from qf_lib.common.utils.returns.avg_drawdown import avg_drawdown
from qf_lib.common.utils.returns.avg_drawdown_duration import avg_drawdown_duration
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.common.utils.returns.cvar import cvar
from qf_lib.common.utils.returns.log_to_simple_return import log_to_simple_return
from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.common.utils.returns.simple_to_log_return import simple_to_log_return
from qf_lib.common.utils.volatility.get_volatility import get_volatility
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.documents_utils.document_exporting.element.table import Table


class TimeseriesAnalysis(TimeseriesAnalysisDTO):
    """
    Used for analysing a timeseries of returns. Calculates and aggregates different statistics of the timeseries,
    It contains the following fields:

    - returns_tms - series of simple returns
    - frequency
    - start_date
    - end_date

    - total_return
    - cagr - annualised return

    - annualised_vol
    - annualised_upside_vol
    - annualised_downside_vol

    - sharpe_ratio
    - omega_ratio
    - calmar_ratio
    - gain_to_pain_ratio
    - sorino_ratio

    - cvar - 5% CVaR expressed related to the specified frequency
    - annualised_cvar - annualised 5% CVaR
    - max_drawdown - maximum drawdown
    - avg_drawdown - average of the whole underwater chart
    - avg_drawdown_duration - average duration of a drawdown

    - best_return
    - worst_return
    - vavg_positive_return
    - avg_negative_return
    - skewness
    - kurtosis
    - kelly

    Parameters
    ----------
    returns_timeseries: QFSeries
        Analysed timeseries. It should be PriceSeries, SimpleReturnSeries or LogReturnSeries
    frequency: Frequency
        Corresponds to the frequency od data samples in the seres.
    """

    def __init__(self, returns_timeseries: QFSeries, frequency: Frequency):
        super().__init__()

        self.returns_tms = returns_timeseries.to_simple_returns()  # type: SimpleReturnsSeries
        self.frequency = frequency
        self.start_date = self.returns_tms.first_valid_index()
        self.end_date = self.returns_tms.index[-1]

        # calculate statistics
        self._calculate_return()
        self._calculate_volatility()
        self._calculate_ratios()
        self._calculate_risk_stats()
        self._calculate_returns_stats()

    # ========= Methods presenting and aggregating results =========

    def populate_table(self, table: Table, name=None) -> None:
        """
        Adds the data calculated in this analysis to the specified table. The table may be brand new or contain other
        analyses of the same kind.

        Parameters
        ----------
        table
            The table to add the data to.
        name
            Name to give this analysis in the columns.
        """
        new_table = Table()

        if name is None:
            name = self.returns_tms.name

        new_table.set_column_names(["Statistic", name])
        for item in self._get_results_list():
            row_name = item[1] + " [" + item[3] + "]"
            if item[3] == '':
                row_name = item[1]

            new_table.add_row([row_name, Table.Cell(item[2])])

        if len(table.rows) != 0:
            new_table = table.combine(new_table)

        table.set_column_names(new_table.get_column_names())
        table.rows = new_table.rows

    @staticmethod
    def values_in_table(ta_collection: Union['TimeseriesAnalysis', Sequence['TimeseriesAnalysis']],
                        asset_names: Union[None, str, Sequence[str]] = None) -> str:
        """Returns a string with all the measures in a form of table of the following format:

                      Asset1    Asset2  ...
        Nice_name1    value11   value21 ... unit1
        Nice_name2    value12   value22 ... unit2
        ...               ...       ... ... unitI
        Nice_nameN    value12   value22 ... unitN

        Parameters
        ------------
        ta_collection
            single TimeseriesAnalysis object or a collection of TimeseriesAnalysis objects
        asset_names
            names of assets corresponding to objects in ta_collection
        """
        if isinstance(ta_collection, TimeseriesAnalysis):
            ta_list = [ta_collection]
        else:
            ta_list = list(ta_collection)

        if isinstance(asset_names, str):
            asset_names = [asset_names]

        # create a header for the table
        if asset_names is None:
            try:
                asset_names = [ta.returns_tms.name for ta in ta_list]
            except AttributeError:
                pass  # no header will be printed if series are without names
        result = ''
        if asset_names is not None:
            names = ''
            for name in asset_names:
                names += '{:>20}'.format(str(name))
            result = '{:24} {}\n'.format("", names)

        first_ta = ta_list[0]

        # create rows
        list_of_rows = []
        for nice_name in first_ta.get_nice_names():
            list_of_rows.append("{:24} ".format(nice_name))

        for ta in ta_list:
            values = ta.get_measures()
            for index, row in enumerate(list_of_rows):
                list_of_rows[index] = row + "{:>20}".format(values[index])

        for index, unit in enumerate(first_ta.get_units()):
            list_of_rows[index] += " {}\n".format(unit)

        for row in list_of_rows:
            result += row

        return result

    @staticmethod
    def table_for_df(df: QFDataFrame, frequency: Frequency = Frequency.DAILY) -> str:
        """Returns a table similar to the one below:

        Analysed period: start_date - end_date, using frequency data
        Name            total_ret        cagr         vol      up_vol    down_vol ...
        Asset1              63.93       28.27       19.15       14.06       14.35 ...
        Asset2              66.26       29.19       20.74       14.86       15.54 ...
        Asset3              66.26       29.19       20.74       14.86       15.54 ...
        ...                   ...         ...         ...         ...         ... ...

        Parameters
        ------------
        df
            DataFrame of returns or prices of assets to be analysed

        frequency
            (optional) frequency of the returns or price sampling in the DataFrame. By default daily frequency is used

        """
        name_ta_list = [(name, TimeseriesAnalysis(asset_tms, frequency)) for name, asset_tms in df.iteritems()]
        first_ta = name_ta_list[0][1]

        result = "Analysed period: {} - {}, using {} data\n".format(
            date_to_str(first_ta.start_date), date_to_str(first_ta.end_date), frequency)

        header_without_dates = ""
        for value in first_ta.get_short_names()[2:]:
            header_without_dates += '{:>12}'.format(value)

        result += ("{:12} {}\n".format("Name", header_without_dates))

        for name, ta in name_ta_list:
            values = ""
            for value in ta.get_measures()[2:]:
                values += '{:>12}'.format(value)
            result += ("{:12} {}\n".format(name.as_string(), values))
        return result

    def get_short_names(self) -> List[str]:
        """
        Returns a list of short names of all the measures
        """
        result = []
        for elements in self._get_results_list():
            result.append(elements[0])
        return result

    def get_nice_names(self) -> List[str]:
        """
        Returns a list of long, nice names of all the measures
        """
        result = []
        for elements in self._get_results_list():
            result.append(elements[1])
        return result

    def get_measures(self) -> List[str]:
        """
        Returns a list of all measures (values)  represented as strings
        """
        result = []
        for elements in self._get_results_list():
            result.append(elements[2])
        return result

    def get_units(self) -> List[str]:
        """
        Returns a list of all units of all measures (values)
        """
        result = []
        for elements in self._get_results_list():
            result.append(elements[3])
        return result

    def _get_results_list(self) -> List[Tuple[str]]:
        """
        Returns
        -------
        List[Tuple[str]]
            the list of tuples. Each tuple corresponds to one property of the timeseries and it is of the following format:
            (short_name, long_name, value, unit)

            short_name: is a short string representation that might be treated as a key and should not have spaces in it
            long_name: it a nice name of the field
            value: is the string representation of the value rounded to 2 decimal places
            unit: is an unit in which the value is expressed. Might be empty.

            All elements of the tuple are strings (including the value, which is a string representation
            of the rounded number)
        """

        def num_to_str(value):
            # represents a default
            return "{:0.2f}".format(value)

        result_list = list()

        result_list.append(('start', 'Start Date', date_to_str(self.start_date), ''))
        result_list.append(('end', 'End Date', date_to_str(self.end_date), ''))

        result_list.append(('total_ret', 'Total Return', num_to_str(self.total_return * 100), '%'))
        result_list.append(('cagr', 'Annualised Return', num_to_str(self.cagr * 100), '%'))

        result_list.append(('vol', 'Annualised Volatility', num_to_str(self.annualised_vol * 100), '%'))
        result_list.append(('up_vol', 'Annualised Upside Vol.', num_to_str(self.annualised_upside_vol * 100), '%'))
        result_list.append(('down_vol', 'Annualised Downside Vol.',
                            num_to_str(self.annualised_downside_vol * 100), '%'))

        result_list.append(('sharpe', 'Sharpe Ratio', num_to_str(self.sharpe_ratio), ''))
        result_list.append(('omega', 'Omega Ratio', num_to_str(self.omega_ratio), ''))
        result_list.append(('calmar', 'Calmar Ratio', num_to_str(self.calmar_ratio), ''))
        result_list.append(('gain/pain', 'Gain to Pain Ratio', num_to_str(self.gain_to_pain_ratio), ''))
        result_list.append(('sorino', 'Sorino Ratio', num_to_str(self.sorino_ratio), ''))

        result_list.append(('cvar', '5% CVaR', num_to_str(self.cvar * 100), '%'))
        result_list.append(('cvar_an', 'Annualised 5% CVaR', num_to_str(self.annualised_cvar * 100), '%'))

        result_list.append(('max_dd', 'Max Drawdown', num_to_str(self.max_drawdown * 100), '%'))
        result_list.append(('avg_dd', 'Avg Drawdown', num_to_str(self.avg_drawdown * 100), '%'))
        result_list.append(('avg_dd_dur', 'Avg Drawdown Duration', num_to_str(self.avg_drawdown_duration), 'days'))

        result_list.append(('best_ret', 'Best Return', num_to_str(self.best_return * 100), '%'))
        result_list.append(('worst_ret', 'Worst Return', num_to_str(self.worst_return * 100), '%'))
        result_list.append(('avg_pos_ret', 'Avg Positive Return', num_to_str(self.avg_positive_return * 100), '%'))
        result_list.append(('avg_neg_ret', 'Avg Negative Return', num_to_str(self.avg_negative_return * 100), '%'))

        result_list.append(('skewness', 'Skewness', num_to_str(self.skewness), ''))
        # result_list.append(('kurtosis', 'Kurtosis', num_to_str(self.kurtosis), ''))
        # result_list.append(('kelly', 'Kelly Value', num_to_str(self.kelly), ''))

        freq_str = str(self.frequency)
        result_list.append(('#observ', 'No. of {} samples'.format(freq_str), len(self.returns_tms), ''))

        return result_list

    # ========= Methods calculating statistics of the timeseries =========

    def _calculate_return(self):
        self.total_return = self.returns_tms.total_cumulative_return()
        self.cagr = cagr(self.returns_tms, self.frequency)

    def _calculate_volatility(self):
        self.annualised_vol = get_volatility(self.returns_tms, self.frequency, annualise=True)

        positive_returns_tms = self.returns_tms[self.returns_tms > 0]
        negative_returns_tms = self.returns_tms[self.returns_tms < 0]

        self.annualised_upside_vol = get_volatility(positive_returns_tms, self.frequency, annualise=True)
        self.annualised_downside_vol = get_volatility(negative_returns_tms, self.frequency, annualise=True)

    def _calculate_ratios(self):
        self.sharpe_ratio = sharpe_ratio(self.returns_tms, self.frequency)
        self.omega_ratio = omega_ratio(self.returns_tms)
        self.calmar_ratio = calmar_ratio(self.returns_tms, self.frequency)
        self.gain_to_pain_ratio = gain_to_pain_ratio(self.returns_tms)
        self.sorino_ratio = sorino_ratio(self.returns_tms, self.frequency)

    def _calculate_risk_stats(self):
        self.cvar = cvar(self.returns_tms, 0.05)  # default is the 5% CVaR
        log_cvar = simple_to_log_return(self.cvar)
        annualised_log_cvar = annualise_with_sqrt(log_cvar, self.frequency)
        self.annualised_cvar = log_to_simple_return(annualised_log_cvar)

        prices_tms = self.returns_tms.to_prices()
        self.max_drawdown = max_drawdown(prices_tms)
        self.avg_drawdown = avg_drawdown(prices_tms)
        self.avg_drawdown_duration = avg_drawdown_duration(prices_tms)

    def _calculate_returns_stats(self):
        self.best_return = max(self.returns_tms)
        self.worst_return = min(self.returns_tms)

        positive_returns = self.returns_tms[self.returns_tms > 0]
        negative_returns = self.returns_tms[self.returns_tms < 0]

        self.percentage_of_positive_returns = positive_returns.count() / self.returns_tms.count()
        self.percentage_of_negative_returns = negative_returns.count() / self.returns_tms.count()

        self.avg_positive_return = positive_returns.mean()
        self.avg_negative_return = negative_returns.mean()

        self.kelly = kelly(self.returns_tms)

        self.skewness = self.returns_tms.skew()
        self.kurtosis = self.returns_tms.kurt()
