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
from typing import Sequence, Union

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.futures.future_tickers.future_ticker import FutureTicker
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib.data_providers.data_provider import DataProvider


class PrefetchingDataProvider(PresetDataProvider):
    """
    Optimises running of the DataProvider by pre-fetching all the data at startup and then using the cached data
    instead of sending over-the-network requests every time the data is requested. If not all data requested
    is available the ValueError will be raised.
    """
    def __init__(self, data_provider: DataProvider,
                 tickers: Union[Ticker, Sequence[Ticker]],
                 fields: Sequence[PriceField],
                 start_date: datetime, end_date: datetime,
                 frequency: Frequency,
                 check_data_availability: bool = True):
        """
        The tickers parameter denotes one or a list of tickers, used further to download the futures contracts related
        data. The list can contain either Tickers or FutureTickers. In case of the Tickers, simply the given fields
        are being downloaded and stored using the PresetDataProvider. In case of the FutureTickers, the future
        chain tickers and their corresponding prices are being downloaded and stored.
        """

        tickers, _ = convert_to_list(tickers, Ticker)
        future_tickers = [ticker for ticker in tickers if isinstance(ticker, FutureTicker)]
        non_future_tickers = [ticker for ticker in tickers if not isinstance(ticker, FutureTicker)]

        all_future_tickers_dict = data_provider.get_futures_chain_tickers(future_tickers)
        all_futures_tickers = [t for tickers_chain in all_future_tickers_dict.values() for t in tickers_chain.values]

        all_tickers = all_futures_tickers + non_future_tickers
        data_array = data_provider.get_price(all_tickers, fields, start_date, end_date, frequency)

        super().__init__(data=data_array,
                         exp_dates=all_future_tickers_dict,
                         start_date=start_date,
                         end_date=end_date,
                         frequency=frequency,
                         check_data_availability=check_data_availability)
