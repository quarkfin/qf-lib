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
from itertools import zip_longest
from typing import Sequence

import numpy as np
from pandas import date_range

from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.common.enums.frequency import Frequency
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class ScenariosGenerator:
    """ Class used for generating different scenarios for Trades. """

    def make_scenarios(self, trade_rets: Sequence[float], scenarios_length: int = 100, num_of_scenarios: int = 10000) \
            -> SimpleReturnsDataFrame:
        """
        Utility function to generate different trades scenarios, where each scenario is a series of returns for a given
        investment strategy.
        The scenarios of a given length are created by randomly choosing (with replacement) returns from the original
        sequence of a Trade's returns. The result is the SimpleReturnsDataFrame which is indexed by the Trade's
        ordinal number and has a scenario in each column.

        Parameters
        ----------
        trade_rets: Sequence[float]
            sequence of floats which represent the returns on Trades performed by some investment strategy
        scenarios_length: int
            number of Trades which should simulated for each scenario
        num_of_scenarios: int
            number of scenarios which should be generated

        Returns
        -------
        SimpleReturnsDataFrame
            data frame of size scenarios_length (rows) by num_of_scenarios (columns). It contains float numbers.
        """
        values = np.random.choice(trade_rets, scenarios_length * num_of_scenarios)
        values = np.reshape(values, (scenarios_length, num_of_scenarios))

        return SimpleReturnsDataFrame(values)

    def make_exposure_scenarios(self, start_date: datetime, end_date: datetime, number_of_trades: int,
                                time_in_the_market: float, exposure: Exposure = Exposure.LONG,
                                frequency: Frequency = Frequency.DAILY, seed: int = None) -> QFSeries:
        """
        Creates a random series, which contains information about the exposure of a certain asset for the given dates
        range. Based on a.o. the total desired number of trades and average holding time of the trades, the function
        generates random trades and fills the rows for corresponding dates with the desired exposure.
        In case if the number of trades provided is too high to create non-adjacent trades, which will together occupy
        <time_in_the_market>% percentage of time, the time span between some of the consecutive trades may be set to 0.
        In that case it may seem as if the returned number of trades was smaller than the expected number of trades.

        Exemplary output for daily trading, 2 trades, time in the market = 60% and desired exposure = LONG:

        2021-10-01     Exposure.OUT
        2021-10-02    Exposure.LONG
        2021-10-03    Exposure.LONG
        2021-10-04    Exposure.LONG
        2021-10-05    Exposure.LONG
        2021-10-06     Exposure.OUT
        2021-10-07     Exposure.OUT
        2021-10-08    Exposure.LONG
        2021-10-09    Exposure.LONG
        2021-10-10     Exposure.OUT

        Parameters
        ----------
        start_date: datetime
            first date considered in the returned series
        end_date: datetime
            last date considered in the returned series
        number_of_trades: int
            total number of trades, which should be generated
        time_in_the_market: float
            total time of the ticker in the market (should be a percentage value, between 0.0 and 1.0)
        exposure: Exposure
            the desired exposure (either short or long)
        frequency: Frequency
            frequency of the trading
        seed: int
            seed used to make the scenarios deterministic

        Returns
        -------
        QFSeries
            Series indexed by dates between start_date and end_date with the given frequency
        """
        assert 0.0 <= time_in_the_market <= 1.0, "time_in_the_market should belong to the [0.0, 1.0] range"
        dates_index = date_range(start_date, end_date, freq=frequency.to_pandas_freq())
        bars_amount = dates_index.size

        bars_in_the_market = round(bars_amount * time_in_the_market)
        if number_of_trades > bars_in_the_market:
            number_of_trades = bars_in_the_market
            warnings.warn(f"The desired number of trades is bigger than the number of bars in the market, which equals "
                          f"time_in_the_market * number of all bars between start_date and end_date. The returned "
                          f"number of trades will be reduced to {number_of_trades}.")

        trades_lengths = self._get_random_integers(bars_in_the_market, number_of_trades, False, seed) \
            if bars_in_the_market > 0 else []

        # Compute the period lengths between the trades
        out_days = bars_amount - bars_in_the_market

        include_zero = out_days < number_of_trades + 1
        days_between_trades = self._get_random_integers(out_days, number_of_trades + 1, include_zero, seed) \
            if out_days > 0 else []

        # Create the timeseries with the randomly generated trading days
        exposures_list = [out * [Exposure.OUT] + long * [exposure] for out, long in
                          zip_longest(days_between_trades, trades_lengths, fillvalue=0)]
        exposures_list = [el for sublist in exposures_list for el in sublist]
        return QFSeries(exposures_list, index=dates_index)

    @staticmethod
    def _get_random_integers(sum_of_values: int, number_of_elements: int, include_zero: bool, seed: int = None):
        """ Create a list of random integers with given sum. """

        # Initialise a random number generator
        rng = np.random.default_rng(seed)
        if not include_zero:
            elements = rng.choice(range(1, sum_of_values), number_of_elements - 1, replace=False).tolist()
        else:
            elements = rng.choice(range(0, sum_of_values + 1), number_of_elements - 1, replace=True).tolist()

        elements = sorted(elements + [0, sum_of_values])
        elements = [t - s for s, t in zip(elements, elements[1:])]

        return elements
