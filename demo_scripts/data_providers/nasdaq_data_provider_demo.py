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

import pandas as pd

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.nasdaq_db_type import NasdaqDBType
from qf_lib.common.tickers.tickers import NasdaqTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.nasdaq.nasdaq_data_provider import NasdaqDataProvider

pd.options.display.max_rows = 100000
pd.options.display.max_columns = 100


def main():
    data_provider = container.resolve(NasdaqDataProvider)  # type: NasdaqDataProvider
    start_date = str_to_date('2016-01-01')
    end_date = str_to_date('2017-11-02')

    print('Single ticker:')
    ticker = NasdaqTicker('IBM', 'WIKI')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Single ticker: lower case')
    ticker = NasdaqTicker('ibm', 'wiki')
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Single ticker:')
    ticker = NasdaqTicker('IBM', 'WIKI/PRICES', NasdaqDBType.Table)
    data = data_provider.get_history(tickers=ticker, start_date=start_date, end_date=end_date)
    print(data)

    print('Single ticker, Price')
    ticker = NasdaqTicker('IBM', 'WIKI/PRICES', NasdaqDBType.Table)
    data = data_provider.get_price(tickers=ticker, fields=PriceField.Close, start_date=start_date, end_date=end_date)
    print(data)


if __name__ == '__main__':
    main()
