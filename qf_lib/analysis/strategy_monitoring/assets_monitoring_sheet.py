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
from typing import List, Union, Dict

import numpy as np
import matplotlib as plt
import pandas as pd
from pandas.core.dtypes.common import is_numeric_dtype

from qf_lib.analysis.strategy_monitoring.pnl_calculator import PnLCalculator
from qf_lib.analysis.common.abstract_document import AbstractDocument

from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.exceptions.future_contracts_exceptions import NoValidTickerException
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.common.utils.error_handling import ErrorHandling
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.futures.futures_chain import FuturesChain
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.data_providers.data_provider import DataProvider
from qf_lib.documents_utils.document_exporting.element.df_table import DFTable
from qf_lib.documents_utils.document_exporting.element.heading import HeadingElement
from qf_lib.documents_utils.document_exporting.element.new_page import NewPageElement
from qf_lib.documents_utils.document_exporting.element.paragraph import ParagraphElement
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.settings import Settings


@ErrorHandling.class_error_logging()
class AssetPerfAndDrawdownSheet(AbstractDocument):
    """
    For each of the given tickers, provides performance and drawdown comparison of the strategy vs buy and hold.
    It also computed the performance contribution and PnL of each of the assets with the given frequency (either yearly
    or monthly).

    Note: It is assumed that at the beginning no positions are open in the portfolio.

    Parameters
    -----------
    category_to_model_tickers: Dict[str, List[Ticker]]
        Dictionary mapping a string, which denotes a category / sector etc, into a list of tickers. The categories are
        used to provide aggregated information about performance contribution in each of them (e.g. to compute
        performance contribution of different sectors, a dictionary mapping sector names into tickers objects).
    transactions: Union[List[Transaction], str]
        Either list of Transaction objects or a path to the Transactions file.
    start_date: datetime
    end_date: datetime
        Dates to used as start and end date for the statistics
    data_provider: DataProvider
        Data provider used to download the prices and future contracts information, necessary to compute Buy and Hold
        benchmark performance
    settings: Settings
        Necessary settings
    pdf_exporter: PDFExporter
        Used to export the document to PDF
    title: str
        Title of the document, will be a part of the filename. Do not use special characters.
    initial_cash: int
        Initial cash in the portfolio (used to compute the performance contribution for each asset)
    frequency: Frequency
        Frequency which should be used to compute the performance contribution. Currently only Yearly and Monthly
        frequencies are supported.
    """

    def __init__(self, category_to_model_tickers: Dict[str, List[Ticker]], transactions: Union[List[Transaction], str],
                 start_date: datetime, end_date: datetime, data_provider: DataProvider, settings: Settings,
                 pdf_exporter: PDFExporter, title: str = "Assets Monitoring Sheet", initial_cash: int = 10000000,
                 frequency: Frequency = Frequency.YEARLY):

        super().__init__(settings, pdf_exporter, title=title)

        self.tickers = [t for tickers_list in category_to_model_tickers.values() for t in tickers_list]
        self._ticker_to_category = {ticker: c for c, tickers_list in category_to_model_tickers.items()
                                    for ticker in tickers_list}

        self._pnl_calculator = PnLCalculator(data_provider)
        self.transactions = self._parse_transactions_file(transactions) if isinstance(transactions, str) \
            else transactions

        self._start_date = start_date
        self._end_date = end_date
        self._data_provider = data_provider
        self._initial_cash = initial_cash

        if frequency not in (Frequency.MONTHLY, Frequency.YEARLY):
            raise NotImplementedError("Only monthly and yearly frequencies are currently supported.")

        self._frequency = frequency
        self._max_columns_per_page = 7
        self._logger = qf_logger.getChild(self.__class__.__name__)

    def build_document(self):
        self._add_header()
        self.document.add_element(ParagraphElement("\n"))

        ticker_to_pnl_series = self._compute_pnl()
        self._add_pnl_and_performance_contribution_tables(ticker_to_pnl_series)
        self._add_performance_statistics(ticker_to_pnl_series)

    def _parse_transactions_file(self, path_to_transactions_file: str) -> List[Transaction]:
        """ Parse the Transactions csv file created by the Monitor and generate a list of transactions objects. """
        ticker_params_to_ticker = {
            (ticker.name, ticker.security_type, ticker.point_value): ticker for ticker in self.tickers
        }

        def get_matching_ticker(row: QFSeries) -> Ticker:
            """ Returns the matching specific ticker. In case if the ticker does not belong to the list of tickers
            passed as the parameter, the transaction is excluded. """
            ticker_str = row.loc["Contract symbol"]
            name = row.loc["Asset Name"]
            sec_type = SecurityType(row.loc["Security type"])
            point_value = row.loc["Contract size"]
            ticker = ticker_params_to_ticker.get((name, sec_type, point_value), None)
            if isinstance(ticker, FutureTicker):
                ticker_type = ticker.supported_ticker_type()
                ticker = ticker_type(ticker_str, sec_type, point_value)
            return ticker

        transactions_df = pd.read_csv(path_to_transactions_file)
        transactions = [Transaction(pd.to_datetime(row.loc["Timestamp"]),
                                    get_matching_ticker(row),
                                    row.loc["Quantity"],
                                    row.loc["Price"],
                                    row.loc["Commission"]) for _, row in transactions_df.iterrows()]
        transactions = [t for t in transactions if t.ticker is not None]
        return transactions

    def _compute_pnl(self) -> Dict[Ticker, PricesSeries]:
        """ Returns a dictionary, which maps tickers into corresponding PnL time series. """
        return {ticker: self._pnl_calculator.compute_pnl(ticker, self.transactions, self._start_date, self._end_date)
                for ticker in self.tickers}

    def _add_performance_statistics(self, ticker_to_pnl_series: Dict[Ticker, PricesSeries]):
        """ Generate performance and drawdown plots, which provide the comparison between the strategy performance
        and Buy and Hold performance for each of the assets. """
        self.document.add_element(NewPageElement())
        self.document.add_element(HeadingElement(level=2, text="Performance and Drawdowns - Strategy vs Buy and Hold"))
        self.document.add_element(ParagraphElement("\n"))

        for ticker in self.tickers:
            grid = self._get_new_grid()
            buy_and_hold_returns = self._generate_buy_and_hold_returns(ticker)

            strategy_exposure_series = ticker_to_pnl_series[ticker].to_simple_returns().fillna(0.0)
            strategy_exposure_series = strategy_exposure_series.where(strategy_exposure_series == 0.0).fillna(1.0)
            strategy_returns = buy_and_hold_returns * strategy_exposure_series
            strategy_returns = strategy_returns.dropna()
            strategy_returns.name = "Strategy"

            if len(strategy_returns) > 0:
                perf_chart = self._get_perf_chart([buy_and_hold_returns, strategy_returns], False,
                                                  "Performance - {}".format(ticker.name))

                underwater_chart = self._get_underwater_chart(strategy_returns.to_prices(),
                                                              title="Drawdown - {}".format(ticker.name),
                                                              benchmark_series=buy_and_hold_returns.to_prices(),
                                                              rotate_x_axis=True)

                grid.add_chart(perf_chart)
                grid.add_chart(underwater_chart)
                self.document.add_element(grid)
            else:
                self._logger.warning("No data is available for {}. No plots will be generated.".format(ticker.name))

    def _generate_buy_and_hold_returns(self, ticker: Ticker) -> SimpleReturnsSeries:
        """ Computes series of simple returns, which would be returned by the Buy and Hold strategy. """
        if isinstance(ticker, FutureTicker):
            try:
                ticker.initialize_data_provider(SettableTimer(self._end_date), self._data_provider)
                futures_chain = FuturesChain(ticker, self._data_provider, FuturesAdjustmentMethod.BACK_ADJUSTED)
                prices_series = futures_chain.get_price(PriceField.Close, self._start_date, self._end_date)
            except NoValidTickerException:
                prices_series = PricesSeries()
        else:
            prices_series = self._data_provider.get_price(ticker, PriceField.Close, self._start_date, self._end_date)

        returns_tms = prices_series.to_simple_returns().replace([-np.inf, np.inf], np.nan).fillna(0.0)
        returns_tms.name = "Buy and Hold"
        return returns_tms

    def _add_pnl_and_performance_contribution_tables(self, ticker_to_pnl: Dict[Ticker, PricesSeries]):
        # For each ticker compute the PnL for each period (each year, month etc)
        pnl_df = QFDataFrame.from_dict(ticker_to_pnl)
        agg_performance = pnl_df.groupby(pd.Grouper(key=pnl_df.index.name, freq=self._frequency.to_pandas_freq())) \
            .apply(lambda s: s.iloc[-1] - s.iloc[0])

        # Format the column labels, so that they point exactly to the considered time frame
        column_labels_format = {
            Frequency.YEARLY: "%Y",
            Frequency.MONTHLY: "%b %Y",
        }
        columns_format = column_labels_format[self._frequency]
        performance_df = agg_performance.rename(index=lambda timestamp: timestamp.strftime(columns_format))

        # Transpose the original data frame, so that performance for each period is presented in a separate column
        performance_df = performance_df.transpose()
        performance_df.index = performance_df.index.set_names("Asset")
        performance_df = performance_df.reset_index()
        performance_df["Asset"] = performance_df["Asset"].apply(lambda t: t.name)

        performance_tables = self._create_performance_tables(performance_df.copy())
        performance_contribution_tables = self._create_performance_contribution_tables(performance_df.copy())

        # Add the text and all figures into the document
        self.document.add_element(HeadingElement(level=2, text="Profit and Loss"))
        self.document.add_element(ParagraphElement("The following tables provide the details on the Total profit and "
                                                   "loss for each asset (notional in currency units)."))
        self.document.add_element(ParagraphElement("\n"))

        for table in performance_tables:
            self.document.add_element(HeadingElement(level=3, text="Performance between: {} - {}".format(
                table.model.data.columns[1], table.model.data.columns[-1])))
            self.document.add_element(table)
            self.document.add_element(ParagraphElement("\n"))

        self.document.add_element(NewPageElement())

        # Add performance contribution table
        self.document.add_element(HeadingElement(level=2, text="Performance contribution"))
        for table in performance_contribution_tables:
            self.document.add_element(HeadingElement(level=3, text="Performance contribution between {} - {}".format(
                table.model.data.columns[1], table.model.data.columns[-1])))
            self.document.add_element(table)

    def _create_performance_tables(self, performance_df: QFDataFrame) -> List[DFTable]:
        """ Create a formatted DFTable out of the performance_df data frame. """
        numeric_columns = [col for col in performance_df.columns if is_numeric_dtype(performance_df[col])]
        performance_df[numeric_columns] = performance_df[numeric_columns].applymap(lambda x: '{:,.0f}'.format(x))
        performance_df = performance_df.set_index("Asset").sort_index()

        # Divide the performance df into a number of data frames, so that each of them contains up to
        # self.max_col_per_page columns, but keep the first column of the original df in all of them
        split_dfs = np.array_split(performance_df, np.ceil(performance_df.num_of_columns / self._max_columns_per_page),
                                   axis=1)
        df_tables = [DFTable(df.reset_index(), css_classes=['table', 'shrink-font', 'right-align', 'wide-first-column'])
                     for df in split_dfs]
        return df_tables

    def _create_performance_contribution_tables(self, performance_df: QFDataFrame) -> List[DFTable]:
        """
        Create a list of DFTables with assets names in the index and different years / months in columns, which contains
        details on the performance contribution for each asset.
        """
        # Create a QFSeries which contains the initial amount of cash in the portfolio for each year / month
        numeric_columns = [col for col in performance_df.columns if is_numeric_dtype(performance_df[col])]
        portfolio_values = performance_df[numeric_columns].sum().shift(fill_value=self._initial_cash).cumsum()
        performance_df[numeric_columns] = performance_df[numeric_columns] / portfolio_values[numeric_columns]

        # Add category column and aggregate data accordingly
        ticker_name_to_category = {t.name: category for t, category in self._ticker_to_category.items()}
        performance_df["Category"] = performance_df["Asset"].apply(lambda t: ticker_name_to_category[t])
        all_categories = list(set(ticker_name_to_category.values()))
        performance_df = performance_df.sort_values(by=["Category", "Asset"])
        performance_df = performance_df.groupby("Category").apply(
            lambda d: pd.concat([PricesDataFrame({**{"Asset": [d.name], "Category": [d.name]},
                                                  **{c: [d[c].sum()] for c in numeric_columns}}), d],
                                ignore_index=True)).drop(columns=["Category"])

        # Add the Total Performance row (divide by 2 as the df contains already aggregated data for each group)
        total_sum_row = performance_df[numeric_columns].sum() / 2
        total_sum_row["Asset"] = "Total Performance"
        performance_df = performance_df.append(total_sum_row, ignore_index=True)

        # Format the rows using the percentage formatter
        performance_df[numeric_columns] = performance_df[numeric_columns].applymap(lambda x: '{:.2%}'.format(x))

        # Divide the performance dataframe into a number of dataframes, so that each of them contains up to
        # self._max_columns_per_page columns
        split_dfs = np.array_split(performance_df.set_index("Asset"),
                                   np.ceil((performance_df.num_of_columns - 1) / self._max_columns_per_page), axis=1)
        df_tables = [DFTable(df.reset_index(), css_classes=['table', 'shrink-font', 'right-align', 'wide-first-column'])
                     for df in split_dfs]

        # Get the indices of rows, which contain category info
        category_indices = performance_df[performance_df["Asset"].isin(all_categories)].index

        for df_table in df_tables:
            # Add table formatting, highlight rows showing the total contribution of the given category
            df_table.add_rows_styles(category_indices, {"font-weight": "bold", "font-size": "0.95em",
                                                        "background-color": "#cbd0d2"})
            df_table.add_rows_styles([performance_df.index[-1]], {"font-weight": "bold", "font-size": "0.95em",
                                                                  "background-color": "#b9bcbd"})
        return df_tables

    def save(self, report_dir: str = ""):
        # Set the style for the report
        plt.style.use(['tearsheet'])
        filename = "%Y_%m_%d-%H%M {}.pdf".format(self.title)
        filename = datetime.now().strftime(filename)

        return self.pdf_exporter.generate([self.document], report_dir, filename)
