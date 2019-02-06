from datetime import datetime
from typing import Sequence

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.data_providers.preset_data_provider import PresetDataProvider
from qf_lib.data_providers.price_data_provider import DataProvider


class PrefetchingDataProvider(PresetDataProvider):
    """
    Optimises running of the DataProvider by pre-fetching all the data at startup and then using the cached data
    instead of sending over-the-network requests every time the data is requested. If not all data requested
    is available the ValueError will be raised.
    """

    def __init__(self, data_provider: DataProvider,
                 tickers: Sequence[Ticker],
                 fields: Sequence[PriceField],
                 start_date: datetime, end_date: datetime,
                 check_data_availability: bool = True):
        prefetched_data = data_provider.get_price(tickers, fields, start_date, end_date)
        super().__init__(
            data=prefetched_data,
            start_date=start_date, end_date=end_date,
            check_data_availability=check_data_availability
        )
