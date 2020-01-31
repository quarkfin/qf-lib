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
from typing import List, Sequence, Union
import pandas as pd

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.futures.future_contract import FutureContract
from qf_lib.containers.futures.future_ticker import FutureTicker
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.series.qf_series import QFSeries


class FuturesChain(pd.Series):
    def __init__(self, future_ticker: FutureTicker, data: List[FutureContract] = None, index: pd.DatetimeIndex = None,
                 dtype=None, name=None, copy=False, fastpath=False):
        """
        The index consists of expiry dates of the future contracts.
        """
        super().__init__(data, index, dtype, name, copy, fastpath)
        self._future_ticker = future_ticker
        self._specific_ticker = future_ticker.ticker
        self.sort_index(inplace=True)

        self._chain = None  # type: PricesDataFrame

    def get_chain(self, start_date: datetime, end_date: datetime,
                  method: FuturesAdjustmentMethod = FuturesAdjustmentMethod.NTH_NEAREST) -> PricesDataFrame:
        """
        Updates the self._chain with new prices.

        At first, the function downloads the prices since the last date, which is available in the chain (self._chain),
        up to the given time. If the downloaded prices data frame / series is empty, the unchanged chain is returned.
        In case if any new prices were returned, it is verified whether any contract expired within this time frame.
        If so - the get_chain function is used to regenerate the chain. The start_date parameter used by the get_chain
        function
        Else - prices are appended to the chain and returned.

        Important note: It regenerates the chain in case if an expiration day occurs. The expiration of a contract is
        stated basing on the specific ticker, which is returned on the given day and the last specific ticker, that
        was returned for this future chain. If these tickers do not match - it is assumed, that the chain has to be
        regenerated.
        """
        try:
            last_date_in_chain = self._chain.index[-1]
        except AttributeError:
            self._chain = self._generate_chain(start_date, end_date, method)
            return self._chain

        # Download the prices since the last date
        fields = list(self._chain.columns)
        prices_df = self._future_ticker.data_handler.get_price(self._future_ticker, fields, last_date_in_chain,
                                                               end_date)
        # Discard the row containing last_date_in_chain
        prices_df = prices_df[1:]
        # If no changes to the PricesDataFrame should be applied return the existing chain
        if prices_df.empty:
            return self._chain.loc[start_date:end_date]

        def expiration_day_occurred() -> bool:
            """
            Returns True if an expiration day, otherwise it returns False.
            """
            return self._specific_ticker != self._future_ticker.ticker

        # Shift the end date to point to the last day in the downloaded prices data frame
        end_date = prices_df.index[-1]

        # Check if between last_date_in_chain and end_date an expiration date occurred
        if expiration_day_occurred():
            # Download data for next FuturesContracts and regenerate the chain
            self._fetch_and_update_futures_contracts(fields, start_date, end_date)
            self._chain = self._generate_chain(start_date, end_date, method)
            self._specific_ticker = self._future_ticker.ticker
            return self._chain
        else:
            # Append the new prices to the existing PricesDataFrame chain
            self._chain = self._chain.append(prices_df)
            self._specific_ticker = self._future_ticker.ticker
            return self._chain.loc[start_date:end_date]

    def update(self, future_chain):
        """
        Updates the current FuturesChain with data acquired from another chain.

        Parameters
        ----------
        future_chain
            Another FuturesChain, that should be merged into the current one
        """

        self.drop(self.index, inplace=True)
        for exp_date in future_chain.index:
            self.loc[exp_date] = future_chain.loc[exp_date]

    def get_ticker(self):
        return self._future_ticker.valid_ticker()

    def _generate_chain(self, start_time: datetime, end_time: datetime,
                        method: FuturesAdjustmentMethod = FuturesAdjustmentMethod.NTH_NEAREST) -> PricesDataFrame:
        """
        Returns a chain of futures, combined together using a certain method.

        Parameters
        ----------
        start_time
        end_time
            the time ranges for the generated future chain
        method
            the method used to combine the the Nth contracts together into one data series, possible methods:
            - NTH_NEAREST - the price data for a certain period of time is taken from the N-th contract, there is no
            discontinuities correction at the contract expiry dates
            - BACK_ADJUST - the historical price discontinuities are corrected, so that they would align smoothly on the
            expiry date. The gaps between consecutive contracts are being adjusted, by shifting the historical data by
            the difference between the Open price on the first day of new contract and Close price on the last day of
            the old contract. The back adjustment considers only the Open, High, Low, Close price values.
            The Volumes are not being adjusted.
        """
        # Verify the parameters values
        N = self._future_ticker.N
        days_before_exp_date = self._future_ticker.days_before_exp_date

        if N < 1 or days_before_exp_date < 1:
            raise ValueError("The number of the contract and the number of days before expiration date should be "
                             "greater than 0.")

        # Shift the index and data according to the start time and end time values. We shift the number of days by 1,
        # so that the days_before_exp_date=1 will use the prices on the expiration date from the newer contract.
        shifted_index = self.index - pd.Timedelta(days=(days_before_exp_date - 1))

        # We use the backfill search for locating the start time, because we will additionally consider the time range
        # between start_time and the found starting expiry date time
        start_time_index_position = shifted_index.get_loc(start_time, method='backfill')

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
            [future.data.loc[left:right] for left, right, future in time_ranges_and_futures])
        # To avoid shifting data on the time ranges, we use overlapping ends and beginnings of the time ranges.
        # Therefore, we need to check if any duplicates exist and on the expiry dates, we keep the data from
        # newer contract
        combined_data_frame = combined_data_frame[~combined_data_frame.index.duplicated(keep='last')]
        combined_data_frame = combined_data_frame.loc[:end_time]

        if method == FuturesAdjustmentMethod.BACK_ADJUSTED:
            # Create the back adjusted series
            # Compute the differences between prices on the expiration days (shifted by the days_before_exp_date
            # number of days). In case if the shifted days in the index contain e.g. saturdays, sundays or other dates
            # that are not in the Future's prices data frame, the first older valid date is taken.
            end_time_index_position = shifted_index.get_loc(end_time, method='pad')

            # In the following slice, in case if end_time == expiry date, we also want to include it in the index
            first_days_of_next_contracts = shifted_index[:end_time_index_position + 1]

            # Apply the back adjustment. Pass the futures chain shifting the data in the way, which will allow to
            # treat the Nth contract as the first element of the data frame
            combined_data_frame = self._back_adjust(first_days_of_next_contracts,
                                                    shifted_data,
                                                    combined_data_frame)

        return combined_data_frame

    def _back_adjust(self, first_day_of_next_contract_index, futures_chain, data_frame):
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
        # lists to the first valid date
        index_of_first_valid_date = next(index for index, item in enumerate(expiration_dates) if not pd.isnull(item))
        expiration_dates = expiration_dates[index_of_first_valid_date:]
        first_day_of_next_contract_index = first_day_of_next_contract_index[index_of_first_valid_date:]
        futures_chain = futures_chain[index_of_first_valid_date:]

        # For each expiry date and corresponding future contract, at first we take the close prices for all dates before
        # the expiry date. Then we take the last row without any NaNs before the provided time value.

        def get_last_close_price(future, time):
            # Returns the last Close price from the data for the given future contract, before a certain time
            # (exclusive)
            try:
                return future.data[PriceField.Close].loc[future.data.index < time].asof(time)
            except IndexError:
                return None
            except TypeError:
                return None

        previous_contracts_close_prices = QFSeries([get_last_close_price(future, time) for time, future in
                                                    zip(first_day_of_next_contract_index, futures_chain)],
                                                   index=expiration_dates)

        def get_first_open_price(future, time):
            # Returns the first Open price from the data for the given future contract, after a certain time (inclusive)
            try:
                index = future.data[PriceField.Open].loc[time:].first_valid_index()
                return future.data[PriceField.Open].loc[time:].loc[index]
            except IndexError:
                return None
            except TypeError:
                return None

        next_contracts_open_prices = QFSeries([get_first_open_price(future, time) for time, future in
                                               zip(first_day_of_next_contract_index, futures_chain[1:])],
                                              index=expiration_dates)

        # We compute the delta values as the difference between the Open prices of the new contracts and Close prices
        # of the old contracts
        delta_values = next_contracts_open_prices - previous_contracts_close_prices
        differences = delta_values.reindex(data_frame.index).fillna(0)

        differences = differences.iloc[::-1].cumsum(axis=0).iloc[::-1]

        for field in [PriceField.Open, PriceField.High, PriceField.Close, PriceField.Low]:
            data_frame[field] = data_frame[field].add(differences)

        return data_frame

    def _fetch_and_update_futures_contracts(self, fields: Union[PriceField, Sequence[PriceField]], start_date: datetime,
                                            end_date: datetime):
        futures_data_dict = self._future_ticker.data_handler.get_futures(self._future_ticker, fields,
                                                                         start_date, end_date)

        self.update(futures_data_dict[self._future_ticker])

