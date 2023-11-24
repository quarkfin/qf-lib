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

from qf_lib.common.enums.price_field import PriceField
from qf_lib.containers.dataframe.prices_dataframe import PricesDataFrame
from qf_lib.containers.series.qf_series import QFSeries


def parabolic_sar(df: PricesDataFrame, acceleration=0.02, max_acceleration=0.2):
    """Computes the parabolic SAR (Stop And Return) indicator for the given dataframe.

    Parameters
    ----------
    df: PricesDataFrame
        PricesDataFrame containing High, Low, Close PriceFields.
    acceleration: float
        Acceleration factor - higher values keep psar values closer to the price line.
    max_acceleration: float
        Limit for the acceleration factor.

    Returns
    -------
    QFSeries
        Series with PSAR values for each index in the dataframe.
    """
    df = df[[PriceField.High, PriceField.Low, PriceField.Close]].dropna()
    high_tms = df[PriceField.High].values
    low_tms = df[PriceField.Low].values
    close_tms = df[PriceField.Close].values

    initial_af = acceleration
    af = initial_af
    sar = close_tms[0] - initial_af * (high_tms[0] - close_tms[0])

    trend = 1  # 1 = positive, -1 = negative trend
    sar_values = []

    for i in range(1, len(df)):
        if trend == 1:
            if close_tms[i] > sar:
                sar = sar + af*(high_tms[i]-sar)
                if high_tms[i] > high_tms[i-1]:
                    af = min(af+initial_af, max_acceleration)
            else:
                trend = -1
                sar = high_tms[i-1]
                af = initial_af
        else:
            if close_tms[i] < sar:
                sar = sar - af*(sar-low_tms[i])
                if low_tms[i] < low_tms[i-1]:
                    af = min(af+initial_af, max_acceleration)
            else:
                trend = 1
                sar = low_tms[i-1]
                af = initial_af
        sar_values.append(sar)

    return QFSeries(sar_values, index=df.index[1:])
