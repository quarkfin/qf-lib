from datetime import datetime
from typing import Union, Sequence

from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.prices_series import PricesSeries
from qf_lib.data_providers.price_data_provider import DataProvider


class FastDataHandler(DataHandler):
    """
    Class pretending to be a DataHandler but being much faster and not protecting from the look-ahead bias (one needs
    to be careful).
    """

    def __init__(self, data_provider: DataProvider, timer: Timer):
        super().__init__(data_provider, timer)

    def historical_price(self, ticker, fields, num_of_bars_needed):
        end_date = self.timer.now()
        start_date = end_date - 2 * RelativeDelta(days=num_of_bars_needed)
        too_much_of_data = self.price_data_provider.get_price(
            ticker, fields, start_date, end_date)  # type: PricesDataFrame
        result = too_much_of_data.tail(num_of_bars_needed)
        return result

    def get_price(self, tickers: Union[Ticker, Sequence[Ticker]], fields: Union[PriceField, Sequence[PriceField]],
                  start_date: datetime, end_date: datetime = None) -> Union[PricesSeries, PricesDataFrame, QFDataArray]:
        return self.price_data_provider.get_price(tickers, fields, start_date, end_date)
