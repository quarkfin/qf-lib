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

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.helpers.create_returns_bar_chart import create_returns_bar_chart

start_date = str_to_date('2000-01-01')
end_date = str_to_date('2016-05-29')

ticker = QuandlTicker('AAPL', 'WIKI')


def main():
    data_provider = container.resolve(GeneralPriceProvider)
    series = data_provider.get_price(ticker, PriceField.Close, start_date=start_date, end_date=end_date)

    annual_rets_chart = create_returns_bar_chart(series)
    annual_rets_chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
