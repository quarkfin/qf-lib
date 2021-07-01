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

import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries
from qf_lib.plotting.helpers.create_line_chart import create_line_chart

num_of_samples = 200
initial_price = 50

dates_index = pd.bdate_range(start='2015-01-01', periods=num_of_samples)


def main():
    values1 = np.random.normal(loc=0.001, scale=0.01, size=num_of_samples)
    returns_tms_1 = SimpleReturnsSeries(values1, index=dates_index)
    prices_tms_1 = returns_tms_1.to_prices(initial_price, frequency=Frequency.DAILY)

    values2 = np.random.normal(loc=0.0, scale=0.01, size=num_of_samples)
    returns_tms_2 = SimpleReturnsSeries(values2, index=dates_index)
    prices_tms_2 = returns_tms_2.to_prices(initial_price, frequency=Frequency.DAILY)

    names = ["Markit PMI", "Official PMI", "50 = no expansion"]

    chart = create_line_chart(
        [prices_tms_1, prices_tms_2], names, "Manufacturing PMI – Markit PMI versus Official PMI", None, [50],
        start_x=datetime.datetime.strptime("2011", "%Y"), dot_decimal_points=0)
    chart.plot()
    plt.show(block=True)


if __name__ == '__main__':
    main()
