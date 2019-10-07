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
from os import path

import matplotlib as plt
from pandas.tseries.frequencies import to_offset
from pandas import Timedelta

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


def error_logging(*exceptions):
    """
    Helper function, used to decorate all the charts plotting functions, in order to facilitate error handling.
    It logs the error message and allows further chart to be plotted successfully.
    """
    logger = qf_logger.getChild(__name__)

    def wrap(func):
        def wrapped_function(*args):
            try:
                return func(*args)
            except exceptions as e:
                logger.error("{}: {}. The chart could not be generated using {}.".format(
                    e.__class__.__name__, e, func.__name__)
                )

        return wrapped_function
    return wrap


class PortfolioTradingSheet(AbstractDocument):
    """
    Creates a PDF containing a visual representation of portfolio changes over time
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, backtest_result: BacktestResult,
                 title: str = "Portfolio Trading Sheet"):
        """
        title
            title of the document, will be a part of the filename. Do not use special characters.
        """
        super().__init__(settings, pdf_exporter, title=title)
        self.backtest_result = backtest_result

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))
        self._add_leverage_chart()
        self._add_assets_number_in_portfolio_chart()
        self._add_concentration_of_portfolio_chart((1, 5,))
        self._add_gini_coefficient_chart()
        self._add_number_of_transactions_chart('D', 'Number of transactions per day')
        self._add_number_of_transactions_chart('30D', 'Number of transactions per moth')
        self._add_number_of_transactions_chart('365D', 'Number of transactions per year')

    def _add_leverage_chart(self):
        lev_chart = self._get_leverage_chart(self.backtest_result.portfolio.leverage())

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        lev_chart.add_decorator(position_decorator)

        self.document.add_element(ChartElement(lev_chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_assets_number_in_portfolio_chart(self):
        assets_history = self.backtest_result.portfolio.assets_history()

        # Find all not NaN values (not NaN values indicate that the position was open for this contract at that time)
        # and count their number for each row (for each of the dates)
        number_of_assets = assets_history.notnull().sum(axis=1)

        assets_number_chart = self._get_line_chart(number_of_assets, "Number of assets in the portfolio")

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        assets_number_chart.add_decorator(position_decorator)

        self.document.add_element(ChartElement(assets_number_chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_concentration_of_portfolio_chart(self, top_assets_numbers: tuple = (1, 5)):
        chart = LineChart(rotate_x_axis=False)

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        # Add top asset contribution
        assets_history = self.backtest_result.portfolio.assets_history()
        assets_history = assets_history.fillna(0)

        # Define a legend
        legend = LegendDecorator(key="legend_decorator")

        for assets_number in top_assets_numbers:
            # For each date (row), find the top_assets largest assets and compute the mean value of their market value
            top_assets_mean_values = assets_history.stack(dropna=False).groupby(level=0).apply(
                lambda group: group.nlargest(assets_number).mean()
            )

            # Divide the computed mean values by the portfolio value, for each of the dates
            top_assets_percentage_value = top_assets_mean_values / self.backtest_result.portfolio.portfolio_values

            concentration_top_asset = DataElementDecorator(top_assets_percentage_value)
            chart.add_decorator(concentration_top_asset)

            # Add to legend
            legend.add_entry(concentration_top_asset, "TOP {} assets".format(assets_number))

        # Add title
        title_decorator = TitleDecorator("Concentration of assets")
        chart.add_decorator(title_decorator)

        # Add legend
        chart.add_decorator(legend)

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    @error_logging(ValueError, AttributeError, IndexError)
    def _add_number_of_transactions_chart(self, pandas_freq: str, title: str):
        chart = LineChart(rotate_x_axis=False)

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        transactions = self.backtest_result.portfolio.transactions_series()

        # Compute the number of transactions per day
        transactions = transactions.resample(Frequency.DAILY.to_pandas_freq()).count()

        # Aggregate the transactions using the given frequency
        if to_offset(pandas_freq) > to_offset('D'):
            transactions = transactions.rolling(pandas_freq).sum()

            # Cut the non complete beginning of the outputs (e.g. in case of 30 days window, cut the first 30 days)
            start_date = transactions.index[0]
            transactions = transactions.loc[start_date + Timedelta(pandas_freq):]
            if transactions.empty:
                raise ValueError("The available time period is too short to compute the statistics with the provided "
                                 "frequency")

        elif to_offset(pandas_freq) < to_offset('D'):
            raise ValueError("The provided pandas frequency can not be higher than the daily frequency")

        transactions_decorator = DataElementDecorator(transactions)
        chart.add_decorator(transactions_decorator)

        # Add title
        title_decorator = TitleDecorator(title)
        chart.add_decorator(title_decorator)

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_gini_coefficient_chart(self):
        chart = LineChart(rotate_x_axis=False)

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        # Get the assets history
        assets_history = self.backtest_result.portfolio.assets_history()
        assets_history = assets_history.fillna(0)

        def gini(group):
            # Function computing the Gini coefficients for each row
            group = group.abs()
            ranks = group.rank(ascending=True)
            mean_value = group.mean()
            samples = group.size
            group = group * (2 * ranks - samples - 1)
            return group.sum() / (samples * samples * mean_value)

        assets_history = assets_history.stack(dropna=False).groupby(level=0).apply(gini).to_frame(name="Gini "
                                                                                                       "coefficient")

        assets_history_decorator = DataElementDecorator(assets_history)
        chart.add_decorator(assets_history_decorator)

        # Add title
        title_decorator = TitleDecorator("Concentration of assets - Gini coefficient")
        chart.add_decorator(title_decorator)

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))


    def save(self, report_dir: str = ""):
        output_sub_dir = path.join(report_dir, "portfolio_trading_sheet")

        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], output_sub_dir, filename)
