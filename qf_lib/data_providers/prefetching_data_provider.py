from datetime import datetime
from typing import Sequence, Union

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
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
        super().__init__(
            data=data_provider.get_price(tickers, fields, start_date, end_date),
            start_date=start_date, end_date=end_date,
            check_data_availability=check_data_availability
        )

    def get_history(
            self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[str, Sequence[str]],
            start_date: datetime, end_date: datetime = None, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        raise NotImplementedError()
