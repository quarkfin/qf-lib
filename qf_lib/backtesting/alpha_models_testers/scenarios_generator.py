from typing import Sequence

import numpy as np
import pandas as pd


class ScenariosGenerator(object):
    """
    Class used for generating different scenarios for Trades. Scenarios are series of returns on Trades for a given
    investment strategy.
    """

    def make_scenarios(
            self, trade_rets: Sequence[float], scenarios_length=100, num_of_scenarios=10000
    ) -> pd.DataFrame:
        """
        Creates a number of scenarios of a given length by randomly choosing (with replacement) returns from
        the original sequence of Trade's returns. The result is the pandas DataFrame which is indexed by the Trade's
        ordinal number and has a scenario in each column.

        Parameters
        ----------
        trade_rets
            sequence of floats which represent the returns on Trades performed by some investment strategy
        scenarios_length
            number of Trades which should simulated for each scenario
        num_of_scenarios
            number of scenarios which should be generated

        Returns
        -------
        DataFrame of size scenarios_length (rows) by num_of_scenarios (columns). It contains float numbers.
        """
        values = np.random.choice(trade_rets, scenarios_length*num_of_scenarios)
        values = np.reshape(values, (scenarios_length, num_of_scenarios))

        return pd.DataFrame(values)
