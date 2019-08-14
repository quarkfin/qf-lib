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

import numpy as np
import pandas as pd

from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.returns.custom_returns_aggregating import aggregate_returns
from qf_lib.containers.series.simple_returns_series import SimpleReturnsSeries


def main():
    start_dates = [str_to_date(date_str) for date_str in ['2017-01-01', '2017-01-05', '2017-01-09']]
    end_dates = [str_to_date(date_str) for date_str in ['2017-02-01', '2017-02-05', '2017-02-09']]

    returns_dates = pd.date_range(start=start_dates[0], end=end_dates[-1], freq='B')
    returns_values = np.random.normal(loc=0.0, scale=0.1, size=len(returns_dates))
    returns_series = SimpleReturnsSeries(returns_values, returns_dates)

    aggregated_returns = aggregate_returns(returns_series, start_dates, end_dates)

    assert (len(aggregated_returns) == len(start_dates))
    assert (len(aggregated_returns) == len(end_dates))


if __name__ == '__main__':
    main()
