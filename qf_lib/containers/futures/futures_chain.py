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
from typing import List
import pandas as pd

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.futures.future import FutureContract
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.series.qf_series import QFSeries


class FuturesChain(pd.Series):
    def __init__(self, data: List[FutureContract] = None, index: pd.DatetimeIndex = None, dtype=None, name=None, copy=False,
                 fastpath=False):
        """
        The index consists of expiry dates of the future contracts.
        """
        super().__init__(data, index, dtype, name, copy, fastpath)
        self.sort_index(inplace=True)

    def get_chain(self, N: int, start_time: datetime, end_time: datetime, days_before_exp_date: int,
                  method: FuturesAdjustmentMethod = FuturesAdjustmentMethod.NTH_NEAREST) -> PricesDataFrame:
        """
        Returns a chain of futures, combined together using a certain method.

        Parameters
        ----------
        N
            the N-th future contract, counting from start_time. We assume the first nearest contract to be the 1st one.
        start_time
        end_time
            the time ranges for the generated future chain
        days_before_exp_date
            the N-th nearest contract considers expiry dates, which are shifted by days_before_exp_date number
            of days - e.g. if days_before_exp_date = 4 and the expiry date = 16th July, then the old contract will be
            returned up to 16 - 4 = 12th July (inclusive) and the new one since 13th July
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
        shifted_data = shifted_data.iloc[(N-1):]

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
        combined_data_frame = pd.concat([future.data.loc[left:right] for left, right, future in time_ranges_and_futures])
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
            first_days_of_next_contracts = shifted_index[:end_time_index_position+1]

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
        expiration_dates = [data_frame.index.asof(date - pd.Timedelta(days=1))
                            for date in first_day_of_next_contract_index]

        # For each expiry date and corresponding future contract, at first we take the close prices for all dates before
        # the expiry date. Then we take the last row without any NaNs before the provided time value.

        def get_last_close_price(future, time):
            # Returns the last Close price from the data for the given future contract, before a certain time
            # (exclusive)
            try:
                return future.data[PriceField.Close].loc[future.data.index < time].asof(time)
            except IndexError:
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

    def get_ticker(self, N: int, date: datetime, days_before_exp_date: int) -> Ticker:
        """
        Returns the ticker of N-th Future Contract for the provided date, assuming that days_before_exp_date days before
        the original expiration the ticker of the next contract will be returned. E.g. if days_before_exp_date = 4 and
        the expiry date = 16th July, then the old contract will be returned up to 16 - 4 = 12th July (inclusive).
        """
        # Shift the index and data according to the start time and end time values.
        shifted_index = self.index - pd.Timedelta(days=days_before_exp_date-1)
        date_index = shifted_index.get_loc(date, method="pad")
        return self.iloc[date_index:].iloc[N].ticker

