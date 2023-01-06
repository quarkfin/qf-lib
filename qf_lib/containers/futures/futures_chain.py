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
from typing import Union, Sequence, Optional, Tuple
import pandas as pd
from numpy import nan

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.futures.future_contract import FutureContract
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.helpers import cast_data_array_to_proper_type


class FuturesChain(pd.Series):
    """Class which facilitates the futures contracts management. Its main functionality is provided by the
    get_price function, which returns a PricesDataFrame (PricesSeries) of prices for the given FutureTicker,
    automatically managing the contracts chaining.

    Parameters
    ------------
    future_ticker: FutureTicker
        The FutureTicker used to download the futures contracts, further chained and joined in order to obtain the
         result of get_price function.
    data_provider: DataProvider
        Reference to the data provider, necessary to download latest prices, returned by the get_price function.
        In case of backtests, the DataHandler wrapper should be used to avoid looking into the future.
    method: FuturesAdjustmentMethod
        FuturesAdjustmentMethod corresponding to one of two available methods of chaining the futures contracts.
    """
    def __init__(self, future_ticker: FutureTicker, data_provider: "DataProvider", method: FuturesAdjustmentMethod =
                 FuturesAdjustmentMethod.NTH_NEAREST):
        """
        The index consists of expiry dates of the future contracts.
        """
        super().__init__(data=None, index=None, dtype=object, name=None, copy=False, fastpath=False)

        self._future_ticker = future_ticker  # type: FutureTicker
        self._data_provider = data_provider  # type: "DataProvider"

        # Used for optimization purposes
        self._specific_ticker = None  # type: str
        self._chain = None  # type: PricesDataFrame
        self._first_cached_date = None  # type: datetime
        self._futures_adjustment_method = method
        self._cached_fields = set()

    def get_price(self, fields: Union[PriceField, Sequence[PriceField]], start_date: datetime, end_date: datetime,
                  frequency: Frequency = Frequency.DAILY) -> Union[PricesDataFrame, PricesSeries]:
        """Combines consecutive specific FutureContracts data, in order to obtain a chain of prices.

        Parameters
        ----------
        fields: PriceField, Sequence[PriceField]
            Data fields, corresponding to Open, High, Low, Close prices and Volume, that should be returned by the function.
        start_date: datetime
            First date for which the chain needs to be created.
        end_date: datetime
            Last date for which the chain needs to be created.
        frequency: Frequency
            Frequency of the returned data, by default set to daily frequency.

        Returns
        ---------
        PricesDataFrame, PricesSeries

        """
        if not self._future_ticker.initialized:
            raise ValueError(f"The future ticker {self._future_ticker} is not initialized with Data Provider and "
                             f"Timer. At first you need to setup them using initialize_data_provider() function.")

        # 1 - Check if the chain was generated at least once, if not - preload the necessary data using the
        # self._preload_data_and_generate_chain function, and then generate the chain of prices,
        # otherwise - store the last and first available dates from the chain
        fields_list, _ = convert_to_list(fields, PriceField)

        if self._chain is not None and not self._chain.empty:
            last_date_in_chain = self._chain.index[-1]
            first_date_in_chain = self._first_cached_date
        else:
            return self._preload_data_and_generate_chain(fields, start_date, end_date, frequency).squeeze()

        # 2 - Check if all the necessary data is available (if start_date >= first_cached_date) and cached fields
        # include all fields from fields_list, if not - preload it by initializing the Futures Chain
        uncached_fields = set(fields_list) - self._cached_fields
        if start_date < first_date_in_chain or uncached_fields:
            self._preload_data_and_generate_chain(fields, start_date, end_date, frequency)

        # 3 - Download the prices since the last date available in the chain
        if last_date_in_chain == end_date:
            return self._chain[fields_list].loc[start_date:end_date].squeeze()

        prices_df: PricesDataFrame = self._data_provider.get_price(self._future_ticker.get_current_specific_ticker(),
                                                                   fields_list, last_date_in_chain, end_date)
        assert isinstance(prices_df, PricesDataFrame)

        # If no changes to the PricesDataFrame should be applied return the existing chain
        if prices_df.empty:
            return self._chain[fields_list].loc[start_date:end_date].squeeze()

        prices_after_last_date_in_chain = prices_df.iloc[1:] if prices_df.index[0] == last_date_in_chain else prices_df
        if prices_after_last_date_in_chain.empty:
            return self._chain[fields_list].loc[start_date:end_date].squeeze()

        # 4 - Check if between last_date_in_chain and end_date an expiration date occurred
        def expiration_day_occurred() -> bool:
            """
            Returns True if an expiration day occurred since last price was added to the chain, otherwise it returns
            False.

            If the price for the last_date_in_chain in self._chain differs from the value for the same date in prices_df
            it means that the expiration day occurred a few days ago, but no data was shifted yet (e.g. it happened on
            saturday and thus there was no new data for the next ticker, which could have been used for data shifting)

            """
            different_ticker = self._specific_ticker != self._future_ticker.ticker

            if last_date_in_chain in prices_df.index:
                different_prices = not self._chain[fields_list].loc[last_date_in_chain].equals(
                    prices_df[fields_list].loc[last_date_in_chain])
            else:
                different_prices = True

            return different_ticker or different_prices

        if expiration_day_occurred():
            # After expiration day the FutureChain has to be regenerated in case of both FuturesAdjustmentMethods, also
            # in case of the N-th nearest contract method.
            # This is caused by the use of last_date_in_chain variable to indicate the beginning of the the prices data
            # frame, that need to be appended to the chain. An exemplary problem may occur in the following situation:

            # Let C1 and C2 denote two consecutive futures contracts, and let C1 expire on the 16th of July. If no
            # prices for C1 will be available since e.g. 13th July (exclusive), then on the 16th July the last_date_in_
            # chain will still point to 13th. Therefore, the prices_df will contain prices for C2 within e.g. 14 - 16th
            # July. As the expiration of C1 occurred on the 16th, the computed prices_df data frame cannot be appended
            # to the chain and the chain should be regenerated.
            return self._preload_data_and_generate_chain(fields, start_date, end_date, frequency).squeeze()
        else:
            # Append the new prices to the existing PricesDataFrame chain
            self._chain = pd.concat([self._chain, prices_after_last_date_in_chain])
            self._specific_ticker = self._future_ticker.ticker
            return self._chain[fields_list].loc[start_date:end_date].squeeze()

    def _preload_data_and_generate_chain(self, fields: Union[PriceField, Sequence[PriceField]], start_date: datetime,
                                         end_date: datetime, frequency: Frequency) -> \
            Union[PricesDataFrame, PricesSeries]:
        """
        Function, which at first preloads all of the necessary data, by initializing the Futures Chain object with
        the self._initialize_futures_chain function. Afterwards, it generates the PricesDataFrame (PricesSeries)
        using the self._generate_chain function and updates the self._specific_ticker. It returns the resulting
        PricesDataFrame (PricesSeries).

        At first, it initializes the FuturesChain with all the necessary data. If the selected futures adjustment
        method is the BACK_ADJUST, verify whether the fields contain the PriceField.Open and PriceField.Close
        and add them if needed.
        """

        fields_list, _ = convert_to_list(fields, PriceField)

        necessary_fields = set(fields_list).union({PriceField.Open, PriceField.Close})
        necessary_fields = necessary_fields.union(self._cached_fields)
        necessary_fields = list(necessary_fields)

        self._initialize_futures_chain(necessary_fields, start_date, end_date, frequency)

        # Generate the PricesDataFrame (PricesSeries)
        self._chain = self._generate_chain(fields, start_date, end_date)

        # Update the specific ticker
        self._specific_ticker = self._future_ticker.ticker
        self._cached_fields = set(fields_list)

        return self._chain[fields_list].loc[start_date:end_date].squeeze()

    def _generate_chain(self, fields, start_time: datetime, end_time: datetime) -> PricesDataFrame:
        """ Returns a chain of futures combined together using a certain method. """
        # Verify the parameters values
        N = self._future_ticker.get_N()
        days_before_exp_date = self._future_ticker.get_days_before_exp_date()
        fields, got_single_field = convert_to_list(fields, PriceField)

        if N < 1 or days_before_exp_date < 1:
            raise ValueError("The number of the contract and the number of days before expiration date should be "
                             "greater than 0.")

        # Shift the index and data according to the start time and end time values. We shift the number of days by 1,
        # so that the days_before_exp_date=1 will use the prices on the expiration date from the newer contract.
        shifted_index = pd.DatetimeIndex(self.index) - pd.Timedelta(days=(days_before_exp_date - 1))
        if shifted_index.empty:
            return PricesDataFrame(columns=fields)

        # We use the backfill search for locating the start time, because we will additionally consider the time range
        # between start_time and the found starting expiry date time
        start_time_index_position = shifted_index.get_indexer([start_time], method='backfill')[0]

        shifted_index = shifted_index[start_time_index_position:]
        shifted_data = self.iloc[start_time_index_position:]
        shifted_data = shifted_data.iloc[(N - 1):]

        # Compute the time ranges for each of the contract. The time ranges should be equal to:
        # [[start_date, exp_date_1 - days_before_exp_date),
        #  [exp_date_1 - days_before_exp_date, exp_date_2 - days_before_exp_date),
        #  [exp_date_2 - days_before_exp_date, exp_date_3 - days_before_exp_date)
        #   ...
        #  [exp_date_K - days_before_exp_date, end_date]]
        # Each of these time ranges is mapped into one contract, from which date within this time would be taken.
        index_left_ranges = [pd.to_datetime(start_time)] + list(shifted_index)
        index_right_ranges = list(shifted_index)

        # Combine the calculated time ranges with the corresponding future contracts. We want the N-th contract
        # to be mapped onto the first time range (start_date, exp_date_1 - days_before_exp_date), N+1-th contract
        # to be mapped onto the second time range etc, therefore we zip the list of both left and ride boundaries
        # of time ranges with a shifted list of contracts.
        time_ranges_and_futures = zip(index_left_ranges, index_right_ranges, shifted_data)

        # Get the data within the desired time ranges from corresponding contracts
        combined_data_frame = pd.concat(
            [future.data.loc[left:right] for left, right, future in time_ranges_and_futures], sort=False)
        # To avoid shifting data on the time ranges, we use overlapping ends and beginnings of the time ranges.
        # Therefore, we need to check if any duplicates exist and on the expiry dates, we keep the data from
        # newer contract
        combined_data_frame = combined_data_frame[~combined_data_frame.index.duplicated(keep='last')]
        combined_data_frame = combined_data_frame.loc[:end_time]

        if self._futures_adjustment_method == FuturesAdjustmentMethod.BACK_ADJUSTED:
            # Create the back adjusted series
            # Compute the differences between prices on the expiration days (shifted by the days_before_exp_date
            # number of days). In case if the shifted days in the index contain e.g. saturdays, sundays or other dates
            # that are not in the Future's prices data frame, the first older valid date is taken.
            end_time_index_position = shifted_index.get_indexer([end_time], method='pad')[0]

            # In the following slice, in case if end_time == expiry date, we also want to include it in the index
            first_days_of_next_contracts = shifted_index[:end_time_index_position + 1]

            # Apply the back adjustment. Pass the futures chain shifting the data in the way, which will allow to
            # treat the Nth contract as the first element of the data frame
            combined_data_frame = self._back_adjust(fields, first_days_of_next_contracts,
                                                    shifted_data, combined_data_frame)

        return combined_data_frame

    def _back_adjust(self, fields, first_day_of_next_contract_index, futures_chain, data_frame):
        """
        Applies back adjustment to the data frame, where the expiration dates are in the exp_dates_index.
        futures_chain contains consecutive futures contract, which should be considered.
        """
        # Define an index, which would point to the dates, when the data correction occurs. In most of the cases it
        # would be the list of expiry dates - 1. However, in case if any of these dates would point to a date, which
        # is not available in the data_frame (e.g. Saturday, Sunday etc.), we would adjust it to point to an older date.
        # We also need to ensure, that the shifted expiration date would not point to the previous contract, which may
        # occur if there would be no price in data_frame for a certain contract (asof in this case will look at the
        # previous contract).

        last_date_with_valid_price = [data_frame.index.asof(date - pd.Timedelta(days=1)) for date in
                                      first_day_of_next_contract_index]

        expiration_dates = list(
            zip(last_date_with_valid_price, [last_date_with_valid_price[0]] + list(first_day_of_next_contract_index))
        )

        expiration_dates = [max(x, y) for x, y in expiration_dates]
        # In case if the first date in the expiration_dates would not be a valid date, but a NaT instead, shift the
        # lists to the first valid date. In case if no valid expiration dates exist (e.g. there is only one price bar)
        # return the original data_frame
        valid_expiration_dates = (index for index, item in enumerate(expiration_dates) if not pd.isnull(item))
        try:
            index_of_first_valid_date = next(valid_expiration_dates)
        except StopIteration:
            return data_frame
        expiration_dates = expiration_dates[index_of_first_valid_date:]
        first_day_of_next_contract_index = first_day_of_next_contract_index[index_of_first_valid_date:]
        futures_chain = futures_chain[index_of_first_valid_date:]

        previous_contracts_close_prices = QFSeries(
            [self._get_last_available_price(future.data, time)
             for time, future in zip(first_day_of_next_contract_index, futures_chain)],
            index=expiration_dates
        )

        next_contracts_open_prices = QFSeries(
            [self._get_first_available_price(future.data, time)
             for time, future in zip(first_day_of_next_contract_index, futures_chain[1:])],
            index=expiration_dates)

        # We compute the delta values as the difference between the Open prices of the new contracts and Close prices
        # of the old contracts
        delta_values = next_contracts_open_prices - previous_contracts_close_prices
        differences = delta_values.reindex(data_frame.index).fillna(0)

        differences = differences.iloc[::-1].cumsum(axis=0).iloc[::-1]

        # Restrict the adjusted fields to Open, High, Low, Close prices
        fields = [f for f in fields if f in (PriceField.Open, PriceField.High, PriceField.Close, PriceField.Low)]

        for field in fields:
            data_frame[field] = data_frame[field].add(differences)

        return data_frame

    @staticmethod
    def _get_last_available_price(data_frame: QFDataFrame, time: datetime):
        """ Return last valid price (either Open or Close price), which was available before <time> (not inclusive). """
        def last_valid_price_and_date(field: PriceField) -> Optional[Tuple[float, datetime, PriceField]]:
            try:
                df = data_frame[data_frame.index < time]
                last_valid_date = df.loc[:, field].last_valid_index()
                return df.loc[last_valid_date, field], last_valid_date, field
            except (IndexError, TypeError, KeyError):
                return None

        valid_dates_and_prices = [last_valid_price_and_date(PriceField.Open),
                                  last_valid_price_and_date(PriceField.Close)]
        valid_dates_and_prices = [e for e in valid_dates_and_prices if e]

        sorted_valid_dates_and_prices = sorted(valid_dates_and_prices, key=lambda e: (e[1], e[2] == PriceField.Close))
        last_valid_price = sorted_valid_dates_and_prices[-1][0] if sorted_valid_dates_and_prices else nan

        return last_valid_price

    @staticmethod
    def _get_first_available_price(data_frame: QFDataFrame, time: datetime):
        """ Return first valid price (either Open or Close price), which was available after <time> (inclusive). """
        def first_valid_price_and_date(field: PriceField) -> Optional[Tuple[float, datetime, PriceField]]:
            try:
                df = data_frame[data_frame.index >= time]
                first_valid_date = df.loc[:, field].first_valid_index()
                return df.loc[first_valid_date, field], first_valid_date, field
            except (IndexError, TypeError, KeyError):
                return None

        valid_dates_and_prices = [first_valid_price_and_date(PriceField.Open),
                                  first_valid_price_and_date(PriceField.Close)]
        valid_dates_and_prices = [e for e in valid_dates_and_prices if e]

        sorted_valid_dates_and_prices = sorted(valid_dates_and_prices, key=lambda e: (e[1], e[2] == PriceField.Close))
        first_valid_price = sorted_valid_dates_and_prices[0][0] if sorted_valid_dates_and_prices else nan

        return first_valid_price

    def _initialize_futures_chain(self, fields: Union[PriceField, Sequence[PriceField]], start_date: datetime,
                                  end_date: datetime, frequency: Frequency):
        """
        Provides data related to the future chain, within a given time range, and updates the Futures Chain with the
        newly acquired data. It gets the values of price fields and expiration dates for each specific future contract.

        It is the first function, that needs to be called, before generating the chain, because it is responsible for
        downloading all the necessary data, used later on by other functions.
        """
        # Check if single field was provided
        _, got_single_field = convert_to_list(fields, PriceField)

        # Get the expiration dates related to the future contracts belonging to the futures chain
        future_tickers_exp_dates_series = self._future_ticker.get_expiration_dates()

        # Consider only these future contracts, which may be used to build the futures chain - do not include contracts,
        # which expired before the start_date
        future_tickers_exp_dates_series = future_tickers_exp_dates_series[
            future_tickers_exp_dates_series.index >= start_date
        ]
        # Exclude contracts which will not be used while building the current futures chain. All of the newer contracts,
        # which will be used for later futures chains building will be downloaded later anyway, as
        # _initialize_futures_chain() is called after each expiration of a contract.
        current_contract_index = pd.Index(future_tickers_exp_dates_series).get_indexer(
            [self._future_ticker.get_current_specific_ticker()]
        )[0]
        last_ticker_position = min(future_tickers_exp_dates_series.size, current_contract_index + 1)
        future_tickers_exp_dates_series = future_tickers_exp_dates_series.iloc[0:last_ticker_position]

        # Download the historical prices
        future_tickers_list = list(future_tickers_exp_dates_series.values)
        futures_data = self._data_provider.get_price(future_tickers_list, fields, start_date, end_date, frequency)

        # Store the start_date used for the purpose of FuturesChain initialization
        self._first_cached_date = start_date

        for exp_date, future_ticker in future_tickers_exp_dates_series.items():

            # Create a data frame and cast it into PricesDataFrame or PricesSeries
            if got_single_field:
                data = futures_data.loc[:, future_ticker]
            else:
                data = futures_data.loc[:, future_ticker, :]
                data = cast_data_array_to_proper_type(data, use_prices_types=True)

            # Check if data is empty (some contract may have no price within the given time range) - if so do not
            # add it to the FuturesChain
            if not data.empty:
                # Create the future object and add it to the Futures Chain data structure
                future = FutureContract(ticker=future_ticker,
                                        exp_date=exp_date,
                                        data=data
                                        )

                self.loc[exp_date] = future

        self.sort_index(inplace=True)
