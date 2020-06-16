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
from itertools import groupby

import matplotlib as plt
from pandas import Timedelta
from pandas.tseries.frequencies import to_offset

from qf_lib.analysis.common.abstract_document import AbstractDocument
from qf_lib.analysis.error_handling import ErrorHandling
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.documents_utils.document_exporting.element.df_table import DFTable
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.element.table import Table
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.plotting.charts.line_chart import LineChart
from qf_lib.plotting.decorators.axes_label_decorator import AxesLabelDecorator
from qf_lib.plotting.decorators.axes_position_decorator import AxesPositionDecorator
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.decorators.legend_decorator import LegendDecorator
from qf_lib.plotting.decorators.title_decorator import TitleDecorator
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
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
        self.full_image_axis_position = (0.08, 0.1, 0.915, 0.80)  # (left, bottom, width, height)

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

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        lev_chart.add_decorator(position_decorator)

        # Add y label
        label_decorator = AxesLabelDecorator(y_label="Leverage")
        lev_chart.add_decorator(label_decorator)

        self.document.add_element(ChartElement(lev_chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_assets_number_in_portfolio_chart(self):
        chart = LineChart(rotate_x_axis=False)
        legend = LegendDecorator(key="legend_decorator")

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        positions_history = self.backtest_result.portfolio.positions_eod_history()

        # Find all not NaN values (not NaN values indicate that the position was open for this contract at that time)
        # and count their number for each row (for each of the dates)
        number_of_contracts = positions_history.notnull().sum(axis=1)
        number_of_contracts_decorator = DataElementDecorator(number_of_contracts)

        chart.add_decorator(number_of_contracts_decorator)
        legend.add_entry(number_of_contracts_decorator, "Contracts")

        # Count number of assets in the portfolio (if on two contracts from same future family exist in the same time,
        # e.g. during rolling day, in the portfolio, they are counted as one asset)
        def contract_to_ticker(c: Contract):
            return self.backtest_result.portfolio.contract_ticker_mapper.\
                contract_to_ticker(c, strictly_to_specific_ticker=False)

        assets_history = positions_history.rename(columns=contract_to_ticker)
        assets_history = assets_history.groupby(level=0, axis=1).apply(func=(
            # For each asset, group all of the corresponding columns (each of which corresponds to one contract),
            # and check if at any given timestamp the "value" of any of the contracts was different than None - this
            # indicates that at this point of time a position concerning the given asset was open in the portfolio
            # (which in the resulting series will be denoted as 1, otherwise - 0, so that it will be possible to
            # sum positions of all open assets at any given point of time)
            lambda x: x.notna().any(axis=1).astype(int)
        ))

        number_of_assets = assets_history.sum(axis=1)
        number_of_assets_decorator = DataElementDecorator(number_of_assets)
        chart.add_decorator(number_of_assets_decorator)
        legend.add_entry(number_of_assets_decorator, "Assets")

        # Add title
        title_decorator = TitleDecorator("Number of assets in the portfolio")
        chart.add_decorator(title_decorator)

        # Add legend
        chart.add_decorator(legend)

        # Add y label
        label_decorator = AxesLabelDecorator(y_label="Number of contracts / assets")
        chart.add_decorator(label_decorator)

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_line_chart_element(self, series, title):
        chart = self._get_line_chart(series, title)

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        self.document.add_element(ChartElement(chart, figsize=self.full_image_size, dpi=self.dpi))

    def _add_concentration_of_portfolio_chart(self, top_assets_numbers: tuple = (1, 5)):
        chart = LineChart(rotate_x_axis=False)

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        # Define a legend
        legend = LegendDecorator(key="legend_decorator")

        # Add y label
        label_decorator = AxesLabelDecorator(y_label="Mean total exposure of top assets")
        chart.add_decorator(label_decorator)

        # Add top asset contribution
        positions_history = self.backtest_result.portfolio.positions_eod_history()
        if positions_history.empty:
            raise ValueError("No positions found in positions history")

        positions_history = positions_history.fillna(0)

        # Map all the single contracts onto tickers (including future tickers) and take the maximal total exposure for
        # each of the groups - in case if two contracts for a single asset will be included in the open positions in
        # the portfolio at any point of time, only one (with higher total exposure) will be considered while generating
        # the top assets plot
        def contract_to_ticker(c: Contract):
            return self.backtest_result.portfolio.contract_ticker_mapper. \
                contract_to_ticker(c, strictly_to_specific_ticker=False)

        assets_history = positions_history.rename(columns=contract_to_ticker)
        assets_history = assets_history.groupby(level=0, axis=1).apply(func=(
            lambda x: x.abs().max(axis=1).astype(float)
        ))

        for assets_number in top_assets_numbers:
            # For each date (row), find the top_assets largest assets and compute the mean value of their market value
            top_assets_mean_values = assets_history.stack(dropna=False).groupby(level=0).apply(
                lambda group: group.nlargest(assets_number).mean()
            )
            # Divide the computed mean values by the portfolio value, for each of the dates
            top_assets_percentage_value = top_assets_mean_values / self.backtest_result.portfolio.portfolio_eod_series()

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

    def _add_number_of_transactions_chart(self, pandas_freq: str, title: str):
        transactions = self.backtest_result.portfolio.transactions_series()
        if transactions.empty:
            raise ValueError("Transactions series is empty")

        # Compute the number of transactions per day
        transactions = transactions.resample(Frequency.DAILY.to_pandas_freq()).count()

        # Aggregate the transactions using the given frequency
        if to_offset(pandas_freq) > to_offset('D'):
            transactions = transactions.rolling(pandas_freq).sum()

            # Cut the non complete beginning of the outputs (e.g. in case of 30 days window, cut the first 30 days)
            start_date = transactions.index[0]
            transactions = transactions.loc[start_date + Timedelta(pandas_freq):]
            if transactions.empty:
                # The available time period is too short to compute the statistics with the provided frequency
                return

        elif to_offset(pandas_freq) < to_offset('D'):
            raise ValueError("The provided pandas frequency can not be higher than the daily frequency")

        self._add_line_chart_element(transactions, title)

    def _add_volume_traded(self):
        transactions = self.backtest_result.portfolio.transactions_series()
        if transactions.empty:
            raise ValueError("Transactions series is empty")

        # Add the chart containing the volume traded in terms of quantity
        quantities = [abs(t.quantity) for t in transactions]
        quantities_series = QFSeries(data=quantities, index=transactions.index)

        # Aggregate the quantities for each day
        quantities_series = quantities_series.resample(Frequency.DAILY.to_pandas_freq()).sum()

        # Generate chart and add it to the document
        self._add_line_chart_element(quantities_series, "Volume traded per day [in contracts]")

        # Add the chart containing the exposure of the traded assets
        total_exposures = [abs(t.quantity) * t.price * t.contract.contract_size for t in transactions]
        total_exposures_series = QFSeries(data=total_exposures, index=transactions.index)
        total_exposures_series = total_exposures_series.resample(Frequency.DAILY.to_pandas_freq()).sum()

        # Generate chart and add it to the document
        self._add_line_chart_element(total_exposures_series, "Volume traded per day [notional in currency units]")

    def _add_gini_coefficient_chart(self):
        chart = LineChart(rotate_x_axis=False)

        position_decorator = AxesPositionDecorator(*self.full_image_axis_position)
        chart.add_decorator(position_decorator)

        # Get the assets history
        assets_history = self.backtest_result.portfolio.positions_eod_history()
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

    def _add_avg_time_in_the_market_per_ticker(self):
        self.document.add_element(NewPageElement())
        self.document.add_element(HeadingElement(level=2, text="Average time in the market per asset"))
        # Get the assets history
        assets_history = self.backtest_result.portfolio.positions_eod_history()
        assets_history = assets_history.fillna(0)

        table = Table(column_names=['Tickers name', 'Longs', 'Shorts', 'Out'], css_class="table stats-table left-align")

        future_contracts = [contract for contract in assets_history.columns if contract.security_type == 'FUT']
        stock_contracts = [contract for contract in assets_history.columns if contract.security_type == 'STK']

        for contract in stock_contracts:
            longs = assets_history[contract].where(assets_history[contract] > 0).count()
            shorts = assets_history[contract].where(assets_history[contract] < 0).count()
            outs = assets_history[contract].where(assets_history[contract] == 0).count()

            number_of_days = longs + shorts + outs
            longs = longs / number_of_days
            shorts = shorts / number_of_days
            outs = outs / number_of_days
            table.add_row([contract.symbol, "{:.2%}".format(longs), "{:.2%}".format(shorts), "{:.2%}".format(outs)])

        # Group the futures contracts by their family ID
        future_contracts.sort(key=lambda contract: contract.symbol)
        for future_ticker, futures_contracts_list in groupby(
                future_contracts,
                lambda c: self.backtest_result.portfolio.contract_ticker_mapper.contract_to_ticker(c, strictly_to_specific_ticker=False)
        ):
            futures_contracts_list = list(futures_contracts_list)

            longs = 0
            shorts = 0
            number_of_days = None

            for contract in futures_contracts_list:
                # It is assumed that no two contracts from the same family create open positions in the same time
                longs += assets_history[contract].where(assets_history[contract] > 0).count()
                shorts += assets_history[contract].where(assets_history[contract] < 0).count()

                if number_of_days is None:
                    number_of_days = assets_history[contract].count()

            outs = number_of_days - longs - shorts

            longs = longs / number_of_days
            shorts = shorts / number_of_days
            outs = outs / number_of_days

            table.add_row([future_ticker.name, "{:.2%}".format(longs), "{:.2%}".format(shorts), "{:.2%}".format(outs)])

        self.document.add_element(table)

    def _add_performance_statistics(self):
        self.document.add_element(NewPageElement())
        self.document.add_element(HeadingElement(level=2, text="Performance of each asset"))

        def contract_to_ticker_name(contract: Contract) -> str:
            contract_ticker_mapper = self.backtest_result.portfolio.contract_ticker_mapper
            ticker = contract_ticker_mapper.contract_to_ticker(contract, strictly_to_specific_ticker=False)
            ticker_name = ticker.name if isinstance(ticker, FutureTicker) else ticker.ticker
            return ticker_name

        # Compute the Profit and loss associated with all trades
        trades_pnl = [
            (contract_to_ticker_name(trade.contract), trade.pnl)
            for trade in self.backtest_result.portfolio.trade_list()
        ]

        # Compute the unrealised Profit and loss associated with all open positions
        open_positions_dict = self.backtest_result.portfolio.open_positions_dict
        open_positions_unrealised_pnl = [
            (contract_to_ticker_name(position.contract()), position.unrealised_pnl)
            for position in open_positions_dict.values()
        ]

        pnl_df = QFDataFrame(data=trades_pnl + open_positions_unrealised_pnl, columns=["Ticker", "Performance"])

        performance_df = pnl_df.groupby(['Ticker'], as_index=False).sum()
        performance_df = performance_df.sort_values(by="Performance", ascending=False)
        performance_df["Performance"] = performance_df["Performance"].apply(lambda pnl: "{:,.2f}".format(pnl))

        table = DFTable(data=performance_df, css_classes=['table', 'left-align', 'slim-table'])
        table.add_columns_classes(["Ticker"], 'wide-column')
        self.document.add_element(table)

    def save(self, report_dir: str = ""):
        # Set the style for the report
        plt.style.use(['tearsheet'])

        filename = "%Y_%m_%d-%H%M Portfolio Trading Sheet.pdf"
        filename = datetime.now().strftime(filename)
        return self.pdf_exporter.generate([self.document], report_dir, filename)
