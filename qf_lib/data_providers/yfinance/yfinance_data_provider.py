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
import warnings
from datetime import datetime
from typing import Set, Type, Union, Sequence, Dict, Optional

from pandas import MultiIndex

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta
from qf_lib.common.utils.dateutils.timer import Timer
from qf_lib.common.utils.miscellaneous.to_list_conversion import convert_to_list
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.containers.series.qf_series import QFSeries
from qf_lib.data_providers.abstract_price_data_provider import AbstractPriceDataProvider
from qf_lib.data_providers.helpers import normalize_data_array
from qf_lib.data_providers.yfinance.yfinance_ticker import YFinanceTicker

try:
    import yfinance as yf

    is_yfinance_intalled = True
except ImportError:
    is_yfinance_intalled = False


class YFinanceDataProvider(AbstractPriceDataProvider):
    """
    Data Provider using the yfinance library to provide historical data of various frequencies.

    Parameters
    -----------
    timer: Timer
        Might be either SettableTimer or RealTimer depending on the use case. If no parameter is passed, a default
        RealTimer object will be used.
    """
    def __init__(self, timer: Optional[Timer] = None):
        super().__init__(timer)

        if not is_yfinance_intalled:
            warnings.warn("yfinance ist not installed. If you would like to use YFinanceDataProvider first install the"
                          " yfinance library.")
            exit(1)

    def price_field_to_str_map(self, *args) -> Dict[PriceField, str]:
        return {
            PriceField.Open: 'Open',
            PriceField.High: 'High',
            PriceField.Low: 'Low',
            PriceField.Close: 'Close',
            PriceField.Volume: 'Volume'
        }

    def get_history(self, tickers: Union[YFinanceTicker, Sequence[YFinanceTicker]], fields: Union[None, str, Sequence[str]],
                    start_date: datetime, end_date: datetime = None, frequency: Frequency = None,
                    look_ahead_bias: bool = False, **kwargs) -> Union[QFSeries, QFDataFrame, QFDataArray]:
        """
        Gets historical attributes (fields) of different securities (tickers).

        Parameters
        ----------
        tickers: YFinanceTicker, Sequence[YFinanceTicker]
            tickers for securities which should be retrieved
        fields: None, str, Sequence[str]
            fields of securities which should be retrieved.
        start_date: datetime
            date representing the beginning of historical period from which data should be retrieved
        end_date: datetime
            date representing the end of historical period from which data should be retrieved;
            if no end_date was provided, by default the current date will be used
        frequency: Frequency
            frequency of the data. This data provider supports Monthly, Weekly, Daily frequencies along with intraday
            frequencies at the following intervals: 60, 30, 15, 5 and 1 minute.
        look_ahead_bias: bool
            if set to False, the look-ahead bias will be taken care of to make sure no future data is returned

        Returns
        -------
        QFSeries, QFDataFrame, QFDataArray, float, str
            If possible the result will be squeezed, so that instead of returning a QFDataArray, data of lower
            dimensionality will be returned. The results will be either a QFDataArray (with 3 dimensions: date, ticker,
            field), a QFDataFrame (with 2 dimensions: date, ticker or field; it is also possible to get 2 dimensions
            ticker and field if single date was provided), a QFSeries (with 1 dimensions: date) or a float / str
            (in case if a single ticker, field and date were provided).
            If no data is available in the database or a non existing ticker was provided an empty structure
            (nan, QFSeries, QFDataFrame or QFDataArray) will be returned.
        """

        frequency = frequency or self.frequency or Frequency.DAILY
        original_end_date = (end_date or self.timer.now()) + RelativeDelta(second=0, microsecond=0)
        # In case of low frequency (daily or lower) shift the original end date to point to 23:59
        if frequency <= Frequency.DAILY:
            original_end_date += RelativeDelta(hour=23, minute=59)

        end_date = original_end_date if look_ahead_bias else (
            self.get_end_date_without_look_ahead(original_end_date, frequency))
        start_date = self._adjust_start_date(start_date, frequency)
        got_single_date = self._got_single_date(start_date, original_end_date, frequency)

        tickers, got_single_ticker = convert_to_list(tickers, YFinanceTicker)
        fields, got_single_field = convert_to_list(fields, (PriceField, str))

        tickers_str = [t.as_string() for t in tickers]
        df = yf.download(list(set(tickers_str)), start_date, end_date, keepna=True,
                         interval=self._frequency_to_period(frequency),
                         progress=False)
        df = df.reindex(columns=MultiIndex.from_product([fields, tickers_str]))
        values = df.values.reshape(len(df), len(tickers), len(fields))
        qf_data_array = QFDataArray.create(df.index.rename("dates"), tickers, fields, values)
        return normalize_data_array(
            qf_data_array, tickers, fields, got_single_date, got_single_ticker, got_single_field, use_prices_types=False
        )

    def supported_ticker_types(self) -> Set[Type[Ticker]]:
        return {YFinanceTicker}

    @staticmethod
    def _frequency_to_period(freq: Frequency):
        frequencies_mapping = {
            Frequency.MIN_1: '1m',
            Frequency.MIN_5: '5m',
            Frequency.MIN_15: '15m',
            Frequency.MIN_30: '30m',
            Frequency.MIN_60: '60m',
            Frequency.DAILY: '1d',
            Frequency.WEEKLY: '1wk',
            Frequency.MONTHLY: '1mo',
            Frequency.QUARTERLY: '3mo',
        }

        try:
            return frequencies_mapping[freq]
        except KeyError:
            raise ValueError(f"Frequency must be one of the supported frequencies: {frequencies_mapping.keys()}.") \
                from None
