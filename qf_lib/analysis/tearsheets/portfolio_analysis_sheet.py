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

import matplotlib as plt
import pandas as pd
from pandas import Timedelta
from pandas.tseries.frequencies import to_offset

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.analysis.trade_analysis.trades_generator import TradesGenerator
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.backtesting.portfolio.backtest_position import BacktestPositionSummary
from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.df_table import DFTable
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
class PortfolioAnalysisSheet(AbstractDocument):
    """
    Creates a PDF containing a visual representation of portfolio changes over time.

    Parameters
    -----------
    settings: Settings
        necessary settings
    pdf_exporter: PDFExporter
        used to export the document to PDF
    backtest_result: BacktestResult
        used to access all trading records
    title: str
        title of the document, will be a part of the filename. Do not use special characters.
    generate_pnl_chart_per_ticker: bool
        If true, adds pnl chart for each asset traded in the portfolio
    """

    def __init__(self, settings: Settings, pdf_exporter: PDFExporter, backtest_result: BacktestResult,
                 title: str = "Portfolio Analysis Sheet", generate_pnl_chart_per_ticker: bool = False):
        super().__init__(settings, pdf_exporter, title=title)
        self.backtest_result = backtest_result
        self.full_image_axis_position = (0.08, 0.1, 0.915, 0.80)  # (left, bottom, width, height)
        self.trades_generator = TradesGenerator()
        self.generate_pnl_chart_per_ticker = generate_pnl_chart_per_ticker
        self.dpi = 200

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))
        self._add_leverage_chart()
        self._add_assets_number_in_portfolio_chart()
        self._add_concentration_of_portfolio_chart((1, 5,))
        self._add_gini_coefficient_chart()
        self._add_number_of_transactions_chart('D', 'Number of transactions per day')
        self._add_number_of_transactions_chart('30D', 'Number of transactions per month')
        self._add_number_of_transactions_chart('365D', 'Number of transactions per year')
        self._add_volume_traded()

        self._add_avg_time_in_the_market_per_ticker()
        self._add_performance_statistics()

    def _add_leverage_chart(self):
        lev_chart = self._get_leverage_chart(self.backtest_result.portfolio.leverage_series())
        lev_chart.add_decorator(AxesPositionDecorator(*self.full_image_axis_position))
        lev_chart.add_decorator(AxesLabelDecorator(y_label="Leverage"))

        self.document.add_element(ChartElement(lev_chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_assets_number_in_portfolio_chart(self):
        chart = LineChart(rotate_x_axis=False)
        chart.add_decorator(AxesPositionDecorator(*self.full_image_axis_position))
        legend = LegendDecorator(key="legend_decorator")

        positions_history = self.backtest_result.portfolio.positions_history()

        # Find all not NaN values (not NaN values indicate that the position was open for this contract at that time)
        # and count their number for each row (for each of the dates)
        number_of_contracts = positions_history.notna().sum(axis=1)
        number_of_contracts_decorator = DataElementDecorator(number_of_contracts)
        chart.add_decorator(number_of_contracts_decorator)
        legend.add_entry(number_of_contracts_decorator, "Contracts")

        # Group tickers by name and for each name and date check if there was at least one position open with any
        # of the corresponding tickers. Finally sum all the assets that had a position open on a certain date.
        number_of_assets = positions_history.groupby(by=lambda ticker: ticker.name, axis='columns') \
            .apply(lambda x: x.notna().any(axis=1)).sum(axis=1)
        number_of_assets_decorator = DataElementDecorator(number_of_assets)
        chart.add_decorator(number_of_assets_decorator)
        legend.add_entry(number_of_assets_decorator, "Assets")

        chart.add_decorator(TitleDecorator("Number of assets in the portfolio"))
        chart.add_decorator(legend)
        chart.add_decorator(AxesLabelDecorator(y_label="Number of contracts / assets"))

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_line_chart_element(self, series, title):
        chart = self._get_line_chart(series, title)
        chart.add_decorator(AxesPositionDecorator(*self.full_image_axis_position))
        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_concentration_of_portfolio_chart(self, top_assets_numbers: tuple = (1, 5)):
        chart = LineChart(rotate_x_axis=False)
        chart.add_decorator(AxesPositionDecorator(*self.full_image_axis_position))
        chart.add_decorator(AxesLabelDecorator(y_label="Mean total exposure of top assets"))
        chart.add_decorator(TitleDecorator("Concentration of assets"))

        legend = LegendDecorator(key="legend_decorator")
        chart.add_decorator(legend)

        # Add top asset contribution
        positions_history = self.backtest_result.portfolio.positions_history()
        if positions_history.empty:
            raise ValueError("No positions found in positions history")

        positions_history = positions_history.applymap(
            lambda x: x.total_exposure if isinstance(x, BacktestPositionSummary) else 0)

        # Group all the tickers by their names and take the maximal total exposure for each of the groups - in case
        # if two contracts for a single asset will be included in the open positions in the portfolio at any point of
        # time, only one (with higher total exposure) will be considered while generating the top assets plot
        assets_history = positions_history.groupby(by=lambda ticker: ticker.name, axis='columns').apply(
            lambda x: x.abs().max(axis=1))

        for assets_number in top_assets_numbers:
            # For each date (row), find the top_assets largest assets and compute the mean value of their market value
            top_assets_mean_values = assets_history.stack(dropna=False).groupby(level=0).apply(
                lambda group: group.nlargest(assets_number).mean()
            ).resample('D').last()
            # Divide the computed mean values by the portfolio value, for each of the dates
            top_assets_percentage_value = top_assets_mean_values / self.backtest_result.portfolio.portfolio_eod_series()

            concentration_top_asset = DataElementDecorator(top_assets_percentage_value)
            chart.add_decorator(concentration_top_asset)
            legend.add_entry(concentration_top_asset, "TOP {} assets".format(assets_number))

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_number_of_transactions_chart(self, pandas_freq: str, title: str):
        transactions = self.backtest_result.transactions
        transactions_series = QFSeries(data=transactions, index=(t.transaction_fill_time for t in transactions))
        if transactions_series.empty:
            raise ValueError("Transactions series is empty")

        # Compute the number of transactions per day
        transactions_series = transactions_series.resample(Frequency.DAILY.to_pandas_freq()).count()

        # Aggregate the transactions using the given frequency
        if to_offset(pandas_freq) > to_offset('D'):
            transactions_series = transactions_series.rolling(pandas_freq).sum()

            # Cut the non complete beginning of the outputs (e.g. in case of 30 days window, cut the first 30 days)
            start_date = transactions_series.index[0]
            transactions_series = transactions_series.loc[start_date + Timedelta(pandas_freq):]
            if transactions_series.empty:
                # The available time period is too short to compute the statistics with the provided frequency
                return

        elif to_offset(pandas_freq) < to_offset('D'):
            raise ValueError("The provided pandas frequency can not be higher than the daily frequency")

        self._add_line_chart_element(transactions_series, title)

    def _add_volume_traded(self):
        transactions = self.backtest_result.transactions
        transactions_series = QFSeries(data=transactions, index=(t.transaction_fill_time for t in transactions))
        if transactions_series.empty:
            raise ValueError("Transactions series is empty")

        # Add the chart containing the volume traded in terms of quantity, aggregated for each day
        quantities = [abs(t.quantity) for t in transactions_series]
        quantities_series = QFSeries(data=quantities, index=transactions_series.index)
        quantities_series = quantities_series.resample(Frequency.DAILY.to_pandas_freq()).sum()
        self._add_line_chart_element(quantities_series, "Volume traded per day [in contracts]")

        # Add the chart containing the exposure of the traded assets
        total_exposures = [abs(t.quantity) * t.price * t.ticker.point_value for t in transactions_series]
        total_exposures_series = QFSeries(data=total_exposures, index=transactions_series.index)
        total_exposures_series = total_exposures_series.resample(Frequency.DAILY.to_pandas_freq()).sum()
        self._add_line_chart_element(total_exposures_series, "Volume traded per day [notional in currency units]")

    def _add_gini_coefficient_chart(self):
        chart = LineChart(rotate_x_axis=False)
        chart.add_decorator(AxesPositionDecorator(*self.full_image_axis_position))

        # Get the assets history
        assets_history = self.backtest_result.portfolio.positions_history()
        assets_history = assets_history.applymap(
            lambda x: x.total_exposure if isinstance(x, BacktestPositionSummary) else 0)

        def gini(group):
            # Function computing the Gini coefficients for each row
            group = group.abs()
            ranks = group.rank(ascending=True)
            mean_value = group.mean()
            samples = group.size
            group = group * (2 * ranks - samples - 1)
            return group.sum() / (samples * samples * mean_value)

        assets_history = assets_history.stack(dropna=False).groupby(level=0).apply(gini).to_frame("Gini coefficient")
        chart.add_decorator(DataElementDecorator(assets_history))
        chart.add_decorator(TitleDecorator("Concentration of assets - Gini coefficient"))

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_avg_time_in_the_market_per_ticker(self):
        """
        Compute the total time in the market per ticker (separately for long and short positions) in minutes
        and divide it by the total duration of the backtest in minutes.
        """
        self.document.add_element(NewPageElement())
        self.document.add_element(HeadingElement(level=2, text="Average time in the market per asset"))

        start_time = self.backtest_result.start_date
        end_time = self.backtest_result.portfolio.timer.now()
        backtest_duration = pd.Timedelta(end_time - start_time) / pd.Timedelta(minutes=1)  # backtest duration in min
        positions_list = self.backtest_result.portfolio.closed_positions() + \
            list(self.backtest_result.portfolio.open_positions_dict.values())

        positions = QFDataFrame(
            data=[(p.ticker().name, p.start_time, (p.end_time or end_time), p.direction()) for p in positions_list],
            columns=["Tickers name", "Start time", "End time", "Position direction"])

        def compute_duration(grouped_rows):
            indexes = [pd.date_range(row["Start time"], row["End time"], freq='T', inclusive='left')
                       for _, row in grouped_rows.iterrows()]

            if len(indexes):
                intervals = indexes[0]
                for index in indexes[1:]:
                    intervals = intervals.union(index)
            else:
                intervals = pd.DatetimeIndex([])

            duration_in_minutes = intervals.size
            return duration_in_minutes / backtest_duration

        positions = positions.groupby(by=["Tickers name", "Position direction"]).apply(compute_duration) \
            .rename("Duration").reset_index()
        positions = positions.pivot_table(index="Tickers name", columns="Position direction",
                                          values="Duration").reset_index()
        positions = positions.rename(columns={-1: "Short", 1: "Long"})

        # Add default 0 column in case if only short / long positions occurred in the backtest
        for column in ["Short", "Long"]:
            if column not in positions.columns:
                positions[column] = 0.0

        positions["Out"] = 1.0 - positions["Long"] - positions["Short"]
        positions[["Long", "Short", "Out"]] = positions[["Long", "Short", "Out"]].applymap(lambda x: '{:.2%}'.format(x))
        positions = positions.fillna(0.0)

        table = DFTable(positions, css_classes=['table', 'left-align'])
        table.add_columns_classes(["Tickers name"], 'wide-column')
        self.document.add_element(table)

    def _add_performance_statistics(self):
        """
        For each ticker computes its overall performance (PnL of short positions, PnL of long positions, total PnL).
        It generates a table containing final PnL values for each of the ticker nad optionally plots the performance
        throughout the backtest.
        """
        closed_positions = self.backtest_result.portfolio.closed_positions()
        closed_positions_pnl = QFDataFrame.from_records(
            data=[(p.ticker().name, p.end_time, p.direction(), p.total_pnl) for p in closed_positions],
            columns=["Tickers name", "Time", "Direction", "Realised PnL"]
        )
        closed_positions_pnl = closed_positions_pnl.sort_values(by="Time")

        # Get all open positions history
        open_positions_history = self.backtest_result.portfolio.positions_history()
        open_positions_history = open_positions_history.reset_index().melt(
            id_vars='index', value_vars=open_positions_history.columns, var_name='Ticker',
            value_name='Position summary')
        open_positions_pnl = QFDataFrame(data={
            "Tickers name": open_positions_history["Ticker"].apply(lambda t: t.name),
            "Time": open_positions_history["index"],
            "Direction": open_positions_history["Position summary"].apply(
                lambda p: p.direction if isinstance(p, BacktestPositionSummary) else 0),
            "Total PnL of open position": open_positions_history["Position summary"].apply(
                lambda p: p.total_pnl if isinstance(p, BacktestPositionSummary) else 0)
        })

        all_positions_pnl = pd.concat([closed_positions_pnl, open_positions_pnl], sort=False)

        performance_dicts_series = all_positions_pnl.groupby(by=["Tickers name"]).apply(
            self._performance_series_for_ticker)
        performance_df = QFDataFrame(performance_dicts_series.tolist(), index=performance_dicts_series.index)

        self.document.add_element(NewPageElement())
        self.document.add_element(HeadingElement(level=2, text="Performance of each asset"))
        final_performance = performance_df. \
            applymap(lambda pnl_series: pnl_series.iloc[-1] if not pnl_series.empty else 0.0). \
            sort_values(by="Overall performance", ascending=False). \
            applymap(lambda p: '{:,.2f}'.format(p)). \
            reset_index()
        table = DFTable(final_performance, css_classes=['table', 'left-align'])
        table.add_columns_classes(["Tickers name"], 'wide-column')
        self.document.add_element(table)

        # Add performance plots
        if self.generate_pnl_chart_per_ticker:
            self.document.add_element(NewPageElement())
            self.document.add_element(
                HeadingElement(level=2, text="Performance of each asset during the whole backtest"))
            for ticker_name, performance in performance_df.iterrows():
                self._plot_ticker_performance(ticker_name, performance)

    def _performance_series_for_ticker(self, df: QFDataFrame):
        df = df.sort_values(by="Time")
        time_index = pd.DatetimeIndex(df[df["Total PnL of open position"].notnull()]["Time"].drop_duplicates())

        plot_lines = [
            ("Long positions", [1]),
            ("Short positions", [-1]),
            ("Overall performance", [0, 1, -1])
        ]

        return_data = {}
        for title, directions in plot_lines:
            open_positions_pnl = df[["Total PnL of open position", "Time", "Direction"]].dropna()
            open_positions_pnl.loc[~open_positions_pnl["Direction"].isin(directions), 'Total PnL of open position'] = 0
            open_positions_pnl = open_positions_pnl.groupby("Time").agg({'Total PnL of open position': 'sum'})

            closed_positions_pnl = df[["Realised PnL", "Time", "Direction"]]
            closed_positions_pnl.loc[~closed_positions_pnl["Direction"].isin(directions), 'Realised PnL'] = 0
            closed_positions_pnl = closed_positions_pnl.groupby("Time").agg({'Realised PnL': 'sum'})
            closed_positions_pnl["Realised PnL"] = closed_positions_pnl["Realised PnL"].cumsum()

            pnl_series = QFSeries(
                data=closed_positions_pnl["Realised PnL"] + open_positions_pnl['Total PnL of open position'],
                index=time_index).fillna(method='ffill').fillna(0.0)
            return_data[title] = pnl_series

        return return_data

    def _plot_ticker_performance(self, ticker_name: str, performance):
        self.document.add_element(HeadingElement(level=2, text="PnL of {}".format(ticker_name)))

        chart = LineChart()
        legend = LegendDecorator(key="legend_decorator")
        line_colors = iter(("#add8e6", "#000000", "#fa8072"))

        for title, pnl_series in performance.iteritems():
            # Plot series only in case if it consist anything else then 0
            if (pnl_series != 0).any():
                data_series = DataElementDecorator(pnl_series, **{"color": next(line_colors)})
                legend.add_entry(data_series, title)
                chart.add_decorator(data_series)

        chart.add_decorator(legend)
        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def save(self, report_dir: str = ""):
        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M Portfolio Analysis Sheet.pdf"
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], report_dir, filename)
