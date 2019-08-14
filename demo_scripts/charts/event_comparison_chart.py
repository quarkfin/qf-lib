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

import matplotlib.pyplot as plt

from demo_scripts.demo_configuration.demo_ioc import container
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.enums.rebase_method import RebaseMethod
from qf_lib.common.tickers.tickers import QuandlTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
from qf_lib.plotting.helpers.create_event_comparison_chart import create_event_comparison_chart

start_date = str_to_date('1996-01-01')
live_start_date = str_to_date('2012-01-01')


def main():
    data_provider = container.resolve(GeneralPriceProvider)
    prices_tms = data_provider.get_price(QuandlTicker('AAPL', 'WIKI'), PriceField.Close, start_date)

    event_dates_list = [datetime(2000, 1, 1), datetime(2003, 1, 1), datetime(2006, 1, 1), datetime(2009, 1, 1)]

    event_chart = create_event_comparison_chart(
        prices_tms, event_dates_list, 'Beginning of the year',
        samples_before=100, samples_after=200, rebase_method=RebaseMethod.divide)
    event_chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
