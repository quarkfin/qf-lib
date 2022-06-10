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
from typing import List, Dict

from pandas import concat, date_range

from qf_lib.backtesting.events.time_event.regular_time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.events.time_event.regular_time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import SettableTimer
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.data_provider import DataProvider


class PnLCalculator:
    def __init__(self, data_provider: DataProvider):
        """
        The purpose of this class is the computation of Profit and Loss for a given ticker, based on a list of
        Transaction objects. The PnL is computed every day, at the AfterMarketCloseEvent time. The calculation requires
        the following events trigger time to be set: AfterMarketCloseEvent (the transactions are analysed on a daily
        basis), MarketOpenEvent and MarketCloseEvent.

        Note: It is assumed that at the beginning no positions are open in the portfolio.

        Parameters
        -----------
        data_provider: DataProvider
            data provider used to download prices data
        """
        self._data_provider = data_provider

    def compute_pnl(self, ticker: Ticker, transactions: List[Transaction], start_date: datetime, end_date: datetime) \
            -> PricesSeries:
        """
        Computes total PnL of a given asset between start_date and end_date. The PnL is computed every day
        at the AfterMarketCloseEvent time.

        Parameters
        ----------
        ticker: Ticker
            Ticker for which the PnL series should be computed. It can be either a normal Ticker or a Future Ticker.
        transactions: List[Transaction]
            List of transactions which should be used to compute the PnL for the Ticker. All transactions that
            correspond to different tickers or where created outside of the start_date - end_date time range are
            discarded.
        start_date: datetime
            First date for which the PnL series should be computed
        end_date: datetime
            Last date for which the PnL series should be computed

        Returns
        -------
        PricesSeries
            series indexed with dates (each date points to the AfterMarketCloseEvent time, so that the order of
            transactions can be preserved), containing the PnL values
        """
        transactions_series = self._filter_transactions(ticker, transactions, start_date, end_date)
        prices_df = self._get_prices_df(ticker, start_date, end_date)
        pnl_series = self._compute_pnl_for_ticker(prices_df, transactions_series, start_date, end_date)
        return pnl_series

    def _get_prices_df(self, ticker: Ticker, start_date: datetime, end_date: datetime) -> PricesDataFrame:
        """ Returns non-adjusted open and close prices, indexed with the Market Open and Market Close time."""
        if isinstance(ticker, FutureTicker):
            ticker.initialize_data_provider(SettableTimer(end_date), self._data_provider)
            tickers_chain = ticker.get_expiration_dates()

            if start_date >= tickers_chain.index[-1] or end_date <= tickers_chain.index[0]:
                # If the futures chain starts after the _end_date or ends before the _start_date - no data available
                return PricesDataFrame()

            # Get all tickers from the chain that were valid between the start_date and expiration date of the
            # currently valid ticker
            end_date = tickers_chain[tickers_chain == ticker.get_current_specific_ticker()].index[0]
            tickers_chain = tickers_chain.loc[start_date:end_date]
            tickers = tickers_chain.values.tolist()

            open_prices = self._data_provider.get_price(tickers, PriceField.Open, start_date, end_date)
            close_prices = self._data_provider.get_price(tickers, PriceField.Close, start_date, end_date)
        else:
            open_prices = self._data_provider.get_price([ticker], PriceField.Open, start_date, end_date)
            close_prices = self._data_provider.get_price([ticker], PriceField.Close, start_date, end_date)

        open_prices.index = [dt + MarketOpenEvent.trigger_time() for dt in open_prices.index]
        close_prices.index = [dt + MarketCloseEvent.trigger_time() for dt in close_prices.index]
        prices = concat([open_prices, close_prices]).sort_index()
        return prices

    def _filter_transactions(self, ticker: Ticker, transactions: List[Transaction], start_date: datetime,
                             end_date: datetime) -> QFSeries:
        """ Filters out transactions, which do not correspond to the given ticker and returns a QFSeries of remaining
        transactions. Only transactions between start_date market open and end_date market close are considered. """
        transactions = [t for t in transactions if start_date + MarketOpenEvent.trigger_time()
                        <= t.transaction_fill_time <= end_date + MarketCloseEvent.trigger_time()]

        if isinstance(ticker, FutureTicker):
            transactions_for_tickers = [t for t in transactions if ticker.belongs_to_family(t.ticker)]
        else:
            transactions_for_tickers = [t for t in transactions if ticker == t.ticker]

        transactions_records = [(t, t.transaction_fill_time) for t in transactions_for_tickers]
        transactions_series = QFDataFrame.from_records(transactions_records, columns=["Transaction", "Index"]) \
            .set_index("Index").iloc[:, 0]
        return transactions_series

    def _compute_pnl_for_ticker(self, prices_df: PricesDataFrame, transactions_series: QFSeries, start_date: datetime,
                                end_date: datetime) -> PricesSeries:
        pnl_values = []
        current_realised_pnl = 0
        ticker_to_position = {}  # type: Dict[Ticker, BacktestPosition]
        prices_df = prices_df.ffill()

        for timestamp in date_range(start_date, end_date, freq="B"):
            timestamp = timestamp + MarketCloseEvent.trigger_time()

            previous_after_market_close = timestamp - RelativeDelta(days=1)
            transactions_for_past_day = transactions_series.loc[previous_after_market_close:timestamp]
            transactions_for_past_day = transactions_for_past_day \
                .where(transactions_for_past_day.index > previous_after_market_close).dropna(how="all")

            for t in transactions_for_past_day:
                position = ticker_to_position.get(t.ticker, BacktestPositionFactory.create_position(t.ticker))
                ticker_to_position[t.ticker] = position

                position.transact_transaction(t)
                if position.is_closed():
                    ticker_to_position.pop(t.ticker)
                    current_realised_pnl += position.total_pnl

            # update prices of all existing positions and get their unrealised pnl
            current_unrealised_pnl = 0.0
            for ticker, position in ticker_to_position.items():
                price = prices_df.loc[:timestamp, ticker].iloc[-1]

                position.update_price(price, price)
                current_unrealised_pnl += position.total_pnl
            pnl_values.append(current_unrealised_pnl + current_realised_pnl)

        return PricesSeries(data=pnl_values, index=date_range(start_date, end_date, freq="B"))
