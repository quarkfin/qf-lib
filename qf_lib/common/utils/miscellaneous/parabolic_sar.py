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

    trend = 1  # 1 = positive, -1 = negative trend
    initial_af = acceleration
    af = initial_af
    psar = df[PriceField.Close][0] - initial_af * (df[PriceField.High][0] - df[PriceField.Close][0])

    def _calculate_psar(row):
        nonlocal trend, psar, af

        if trend == 1:
            continue_trend = row[PriceField.Close] > psar
            psar = psar + af * (row[PriceField.High] - psar) * continue_trend
            af = min(af + initial_af, max_acceleration) if row[PriceField.High] > row['high_shifted'] else af
            if not continue_trend:
                trend = -1
                af = initial_af
                psar = row['high_shifted']
        else:
            continue_trend = row[PriceField.Close] < psar
            psar = psar - af * (psar - row[PriceField.Low]) * continue_trend
            af = min(af + initial_af, max_acceleration) if row[PriceField.Low] < row['low_shifted'] else af
            if not continue_trend:
                trend = 1
                af = initial_af
                psar = row['low_shifted']

        return psar

    df['high_shifted'] = df[PriceField.High].shift(1)
    df['low_shifted'] = df[PriceField.Low].shift(1)

    return QFSeries(df[1:].apply(_calculate_psar, axis=1), index=df.index[1:])
