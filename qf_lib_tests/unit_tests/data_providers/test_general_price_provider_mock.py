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

import unittest

import pandas as pd
from mockito import mock, when

from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker, BloombergTicker, HaverTicker, CcyTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.qf_data_array import QFDataArray
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider


class TestGeneralPriceProviderMock(unittest.TestCase):
    START_DATE = str_to_date('2017-10-02')
    END_DATE = str_to_date('2017-10-17')

    BBG_TICKERS = [BloombergTicker('BBG1'), BloombergTicker('BBG2'),
                   BloombergTicker('BBG3'), BloombergTicker('BBG4')]

    QUANDL_TICKERS = [QuandlTicker('Quandl1', 'DB'), QuandlTicker('Quandl2', 'DB'),
                      QuandlTicker('Quandl3', 'DB'), QuandlTicker('Quandl4', 'DB')]

    HAVER_TICKERS = [HaverTicker('Haver1', 'DB'), HaverTicker('Haver2', 'DB'),
                     HaverTicker('Haver3', 'DB'), HaverTicker('Haver4', 'DB')]

    CCY_TICKERS = [CcyTicker("Bitcoin"), CcyTicker("Ripple"),
                   CcyTicker("Etherium"), CcyTicker("NEM")]

    SINGLE_PRICE_FIELD = PriceField.Close
    PRICE_FIELDS = [SINGLE_PRICE_FIELD]

    NUM_OF_DATES = 12

    def setUp(self):

        datetime_index = pd.DatetimeIndex([
            '2017-10-02', '2017-10-03', '2017-10-04', '2017-10-05', '2017-10-06',
            '2017-10-09', '2017-10-10', '2017-10-11', '2017-10-12', '2017-10-13',
            '2017-10-16', '2017-10-17'
        ])

        data = [
            [[263.7628], [None],   [111.02], [321.8249]],
            [[263.9803], [106.39], [121.29], [322.0949]],
            [[264.1640], [106.36], [121.22], [322.3203]],
            [[264.0932], [106.25], [121.05], [322.4172]],
            [[263.9816], [106.12], [120.95], [322.1411]],
            [[263.9816], [106.24], [121.05], [None]],
            [[264.4529], [106.28], [121.13], [None]],
            [[264.5108], [106.40], [121.07], [322.3553]],
            [[264.8223], [106.50], [121.10], [322.7489]],
            [[264.4531], [106.23], [121.31], [322.9710]],
            [[264.4690], [106.16], [121.14], [323.0688]],
            [[None],     [106.06], [121.01], [323.1553]]
        ]

        bloomberg = mock(strict=True)
        when(bloomberg)\
            .get_price(self.BBG_TICKERS, self.PRICE_FIELDS, self.START_DATE, self.END_DATE)\
            .thenReturn(
                QFDataArray.create(dates=datetime_index, tickers=self.BBG_TICKERS, fields=self.PRICE_FIELDS, data=data)
            )
        when(bloomberg).supported_ticker_types().thenReturn({BloombergTicker})

        quandl = mock(strict=True)
        when(quandl)\
            .get_price(self.QUANDL_TICKERS, self.PRICE_FIELDS, self.START_DATE, self.END_DATE)\
            .thenReturn(
                QFDataArray.create(
                    dates=datetime_index, tickers=self.QUANDL_TICKERS, fields=self.PRICE_FIELDS, data=data
                )
            )
        when(quandl).supported_ticker_types().thenReturn({QuandlTicker})

        haver = mock(strict=True)
        when(haver)\
            .get_price(self.HAVER_TICKERS, self.PRICE_FIELDS, self.START_DATE, self.END_DATE) \
            .thenReturn(
                QFDataArray.create(
                    dates=datetime_index, tickers=self.HAVER_TICKERS, fields=self.PRICE_FIELDS, data=data
                )
            )
        when(haver).supported_ticker_types().thenReturn({HaverTicker})

        ccy = mock(strict=True)
        when(ccy)\
            .get_price(self.CCY_TICKERS, self.PRICE_FIELDS, self.START_DATE, self.END_DATE) \
            .thenReturn(
                QFDataArray.create(
                    dates=datetime_index, tickers=self.CCY_TICKERS, fields=self.PRICE_FIELDS, data=data
                )
            )
        when(ccy).supported_ticker_types().thenReturn({CcyTicker})

        self.price_provider = GeneralPriceProvider(bloomberg, quandl, haver, ccy)

    # =========================== Test get_price method ==========================================================

    def test_price_single_provider_single_field(self):
        data = self.price_provider.get_price(tickers=self.QUANDL_TICKERS, fields=self.SINGLE_PRICE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE)

        self.assertEqual(PricesDataFrame, type(data))
        self.assertEqual((self.NUM_OF_DATES, len(self.QUANDL_TICKERS)), data.shape)
        self.assertEqual(list(data.columns), self.QUANDL_TICKERS)

    def test_price_multiple_providers_single_field(self):
        tickers = self.BBG_TICKERS + self.QUANDL_TICKERS + self.HAVER_TICKERS
        data = self.price_provider.get_price(tickers=tickers, fields=self.SINGLE_PRICE_FIELD,
                                             start_date=self.START_DATE, end_date=self.END_DATE)
        self.assertEqual(type(data), PricesDataFrame)
        self.assertEqual(data.shape, (self.NUM_OF_DATES, len(tickers)))
        self.assertEqual(list(data.columns), tickers)


if __name__ == '__main__':
    unittest.main()
