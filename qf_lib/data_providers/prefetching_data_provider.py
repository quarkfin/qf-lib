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
from typing import Sequence, Union, Optional

from qf_lib.common.enums.expiration_date_field import ExpirationDateField

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.data_providers.exchange_rate_provider import ExchangeRateProvider
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.futures_data_provider import FuturesDataProvider
from qf_lib.data_providers.helpers import chain_tickers_within_range
from qf_lib.data_providers.preset_data_provider import PresetDataProvider


class PrefetchingDataProvider(PresetDataProvider):
    """
    Optimises running of the DataProvider by pre-fetching all the data at startup and then using the cached data
    instead of sending over-the-network requests every time the data is requested. If not all data requested
    is available the ValueError will be raised.

    Parameters
    -----------
    data_provider: AbstractPriceDataProvider
        data provider used to download the data
    tickers: Ticker, Sequence[Ticker]
        one or a list of tickers, used further to download the futures contracts related data.
        The list can contain either Tickers or FutureTickers. In case of the Tickers, simply the given fields
        are being downloaded and stored using the PresetDataProvider. In case of the FutureTickers, the future
        chain tickers and their corresponding prices are being downloaded and stored.
    fields: PriceField, Sequence[PriceField]
        fields that should be downloaded
    start_date: datetime
        first date to be downloaded
    end_date: datetime
        last date to be downloaded
    frequency: Frequency
        frequency of the data
    """

    def __init__(self, data_provider: AbstractPriceDataProvider,
                 tickers: Union[Ticker, Sequence[Ticker]],
                 fields: Union[PriceField, Sequence[PriceField]],
                 start_date: datetime, end_date: datetime,
                 frequency: Frequency, timer: Optional[Timer] = None):

        self.data_provider = data_provider
        self.logger = qf_logger.getChild(self.__class__.__name__)

        # Convert fields into list in order to return a QFDataArray as the result of get_price function
        fields, _ = convert_to_list(fields, PriceField)

        # Convert the tickers to list and remove duplicates
        tickers, _ = convert_to_list(tickers, Ticker)
        tickers = list(dict.fromkeys(tickers))

        future_tickers = [ticker for ticker in tickers if isinstance(ticker, FutureTicker)]
        non_future_tickers = [ticker for ticker in tickers if not isinstance(ticker, FutureTicker)]

        exp_dates = None
        all_tickers = non_future_tickers

        if future_tickers:
            if not isinstance(data_provider, FuturesDataProvider):
                self.logger.error("The passed data provider does not support future tickers. All future tickers will "
                                  "be ignored in the process.")
            else:
                exp_dates = data_provider.get_futures_chain_tickers(future_tickers, ExpirationDateField.all_dates())

                # Filter out all these specific future contracts, which expired before start_date
                for ft in future_tickers:
                    all_tickers.extend(chain_tickers_within_range(ft, exp_dates[ft], start_date, end_date))

        data_array = data_provider.get_price(all_tickers, fields, start_date, end_date, frequency, timer)

        super().__init__(data=data_array,
                         exp_dates=exp_dates,
                         start_date=start_date,
                         end_date=end_date,
                         frequency=frequency,
                         timer=timer)

    def get_last_available_exchange_rate(self, base_currency, quote_currency, frequency):
        if isinstance(self.data_provider, ExchangeRateProvider):
            return self.data_provider.get_last_available_exchange_rate(base_currency, quote_currency, frequency)
        else:
            raise NotImplementedError(f"{type(self.data_provider)} does not extend ExchangeRateProvider.")
