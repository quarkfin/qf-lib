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
#
import unittest

import pandas as pd

from demo_scripts.common.utils.dummy_ticker import DummyTicker
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.futures.future import FutureContract
from qf_lib.containers.futures.futures_adjustment_method import FuturesAdjustmentMethod
from qf_lib.containers.futures.futures_chain import FuturesChain


class TestBloombergFutures(unittest.TestCase):

    def setUp(self):
        self.dates = pd.date_range(start='1/1/2019', periods=20)
        self.expiration_dates = pd.date_range(start='1/5/2019', freq='5D', periods=4)
        self.futures_chain = FuturesChain(data=self._mock_data(), index=self.expiration_dates)
        self.fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]

    def _mock_data(self):
        base_data = [100, 110, 95, 102, 1000]
        data = [[d + 10 * i*(-1)**i for d in base_data] for i in range(len(self.expiration_dates))]

        futures = []

        for exp_date, first_data_row in zip(self.expiration_dates, data):
            fields = PriceField.ohlcv()
            raw_data = [
                [d + 2*i + 5*(-1)**i for d in first_data_row] for i in range(len(self.dates))
            ]
            futures.append(
                FutureContract(DummyTicker('A'), exp_date, PricesDataFrame(index=self.dates, data=raw_data, columns=fields))
            )
        return futures

    # Nth nearest future contract

    def test_1st_nearest_on_expiry_date(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-15')

        # Get the first future contracts, set the days before expiry to 1
        chain = self.futures_chain.get_chain(1, start_date, end_date, 1)

        for i in range(len(self.futures_chain) - 1):
            contract_1 = self.futures_chain.iloc[i]
            contract_2 = self.futures_chain.iloc[i+1]

            exp_date = contract_1.exp_date
            before_exp_date = exp_date - pd.Timedelta(days=1)

            # On the expiry date the newer contract should be taken
            self.assertCountEqual(chain.loc[exp_date], contract_2.data.loc[exp_date])

            # Day before the expiry date the older contract should be taken
            self.assertCountEqual(chain.loc[before_exp_date], contract_1.data.loc[before_exp_date])

    def test_1st_nearest_with_4_days_before_exp_date(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-20')

        days_before_exp_date = 4

        # Get the first future contracts, set the days before expiry to days_before_exp_date
        chain = self.futures_chain.get_chain(1, start_date, end_date, days_before_exp_date)

        for i in range(len(self.futures_chain) - 1):
            contract_1 = self.futures_chain.iloc[i]
            contract_2 = self.futures_chain.iloc[i + 1]

            exp_date = contract_1.exp_date - pd.Timedelta(days=3)
            before_exp_date = exp_date - pd.Timedelta(days=1)

            # On the expiry date the newer contract should be taken
            self.assertCountEqual(chain.loc[exp_date], contract_2.data.loc[exp_date])

            # Day before the expiry date the older contract should be taken
            self.assertCountEqual(chain.loc[before_exp_date], contract_1.data.loc[before_exp_date])

    def test_2nd_nearest_on_expiry_date(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-20')

        # Get the second future contracts, set the days before expiry to 1
        chain = self.futures_chain.get_chain(2, start_date, end_date, 1)

        for i in range(len(self.futures_chain) - 2):
            contract_1 = self.futures_chain.iloc[i]
            contract_2 = self.futures_chain.iloc[i + 1]
            contract_3 = self.futures_chain.iloc[i + 2]

            exp_date = contract_1.exp_date
            before_exp_date = exp_date - pd.Timedelta(days=1)

            # On the expiry date the third contract should be taken
            self.assertCountEqual(chain.loc[exp_date], contract_3.data.loc[exp_date])

            # Day before the expiry date the second contract should be taken
            self.assertCountEqual(chain.loc[before_exp_date], contract_2.data.loc[before_exp_date])

    def test_2nd_nearest_with_4_days_before_exp_date(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-20')

        days_before_exp_date = 4

        # Get the second future contracts, set the days before expiry to days_before_exp_date
        chain = self.futures_chain.get_chain(2, start_date, end_date, days_before_exp_date)

        for i in range(len(self.futures_chain) - 2):
            contract_1 = self.futures_chain.iloc[i]
            contract_2 = self.futures_chain.iloc[i + 1]
            contract_3 = self.futures_chain.iloc[i + 2]

            exp_date = contract_1.exp_date - pd.Timedelta(days=3)
            before_exp_date = exp_date - pd.Timedelta(days=1)

            # On the expiry date the third contract should be taken
            self.assertCountEqual(chain.loc[exp_date], contract_3.data.loc[exp_date])

            # Day before the expiry date the second contract should be taken
            self.assertCountEqual(chain.loc[before_exp_date], contract_2.data.loc[before_exp_date])

    # Back adjustment
    def test_1st_nearest_on_expiry_date_back_adjust(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-14')

        chain = self.futures_chain.get_chain(1, start_date, end_date, 1, FuturesAdjustmentMethod.BACK_ADJUSTED)

        # Check on the 10th - 14th January 2019. The first nearest contract is the one, that expires on
        # the 15th January.
        for date in pd.date_range(start='2019-01-10', end='2019-01-14'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  self.futures_chain.iloc[2].data[self.fields].loc[date])

        # 10th January was the day, when one of the futures expired (self.futures_chain.iloc[1]). On the 9th January
        # the price in the chain should be back adjusted.

        delta = self.futures_chain.iloc[2].data[PriceField.Open].loc[str_to_date('2019-01-10')] - \
                self.futures_chain.iloc[1].data[PriceField.Close].loc[str_to_date('2019-01-09')]

        for date in pd.date_range(start='2019-01-05', end='2019-01-09'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[1].data[self.fields].loc[date])
        # Test the next expiry date
        delta += (self.futures_chain.iloc[1].data[PriceField.Open].loc[str_to_date('2019-01-05')] -
                  self.futures_chain.iloc[0].data[PriceField.Close].loc[str_to_date('2019-01-04')])

        for date in pd.date_range(start='2019-01-01', end='2019-01-04'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[0].data[self.fields].loc[date])

    def test_2nd_nearest_on_expiry_date_back_adjust(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-14')

        chain = self.futures_chain.get_chain(2, start_date, end_date, 1, FuturesAdjustmentMethod.BACK_ADJUSTED)

        for date in pd.date_range(start='2019-01-10', end='2019-01-14'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  self.futures_chain.iloc[3].data[self.fields].loc[date])

        delta = self.futures_chain.iloc[3].data[PriceField.Open].loc[str_to_date('2019-01-10')] - \
                self.futures_chain.iloc[2].data[PriceField.Close].loc[str_to_date('2019-01-09')]

        for date in pd.date_range(start='2019-01-05', end='2019-01-09'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[2].data[self.fields].loc[date])

        # Test the next expiry date

        delta += (self.futures_chain.iloc[2].data[PriceField.Open].loc[str_to_date('2019-01-05')] -
                  self.futures_chain.iloc[1].data[PriceField.Close].loc[str_to_date('2019-01-04')])

        for date in pd.date_range(start='2019-01-01', end='2019-01-04'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[1].data[self.fields].loc[date])

    def test_1st_nearest_4_days_before_exp_date_back_adjust(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-14')

        days_before_exp_date = 4

        chain = self.futures_chain.get_chain(1, start_date, end_date, days_before_exp_date,
                                             FuturesAdjustmentMethod.BACK_ADJUSTED)

        for date in pd.date_range(start='2019-01-12', end='2019-01-14'):
            self.assertCountEqual(chain[self.fields].loc[date], self.futures_chain.iloc[3].data[self.fields].loc[date])

        delta = self.futures_chain.iloc[3].data[PriceField.Open].loc[str_to_date('2019-01-12')] - \
                self.futures_chain.iloc[2].data[PriceField.Close].loc[str_to_date('2019-01-11')]

        for date in pd.date_range(start='2019-01-07', end='2019-01-11'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[2].data[self.fields].loc[date])

        delta += (self.futures_chain.iloc[2].data[PriceField.Open].loc[str_to_date('2019-01-07')] -
                  self.futures_chain.iloc[1].data[PriceField.Close].loc[str_to_date('2019-01-06')])

        for date in pd.date_range(start='2019-01-02', end='2019-01-06'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[1].data[self.fields].loc[date])

        delta += (self.futures_chain.iloc[1].data[PriceField.Open].loc[str_to_date('2019-01-02')] -
                  self.futures_chain.iloc[0].data[PriceField.Close].loc[str_to_date('2019-01-01')])

        for date in pd.date_range(start='2019-01-01', end='2019-01-01'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[0].data[self.fields].loc[date])

    def test_2nd_nearest_on_4_days_before_exp_date_back_adjust(self):
        start_date = str_to_date('2019-01-01')
        end_date = str_to_date('2019-01-11')

        chain = self.futures_chain.get_chain(2, start_date, end_date, 4, FuturesAdjustmentMethod.BACK_ADJUSTED)

        for date in pd.date_range(start='2019-01-07', end='2019-01-11'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  self.futures_chain.iloc[3].data[self.fields].loc[date])

        delta = (self.futures_chain.iloc[3].data[PriceField.Open].loc[str_to_date('2019-01-07')] -
          self.futures_chain.iloc[2].data[PriceField.Close].loc[str_to_date('2019-01-06')])

        for date in pd.date_range(start='2019-01-02', end='2019-01-06'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[2].data[self.fields].loc[date])

        delta += (self.futures_chain.iloc[2].data[PriceField.Open].loc[str_to_date('2019-01-02')] -
                  self.futures_chain.iloc[1].data[PriceField.Close].loc[str_to_date('2019-01-01')])

        for date in pd.date_range(start='2019-01-01', end='2019-01-01'):
            self.assertCountEqual(chain[self.fields].loc[date],
                                  delta + self.futures_chain.iloc[1].data[self.fields].loc[date])


if __name__ == '__main__':
    unittest.main()


