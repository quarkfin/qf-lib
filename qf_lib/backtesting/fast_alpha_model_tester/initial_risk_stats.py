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

from typing import Sequence

import numpy as np
import pandas as pd

from qf_lib.common.utils.returns.max_drawdown import max_drawdown
from qf_lib.containers.dataframe.cast_dataframe import cast_dataframe
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame


class InitialRiskStatsFactory:
    FAILED = "Failed"
    SUCCEEDED = "Succeeded"

    def __init__(self, max_accepted_dd: float, target_return: float):
        assert max_accepted_dd > 0, "Draw-down should be a positive number"

        self._max_accepted_dd = max_accepted_dd
        self._target_return = target_return

    def make_stats(self, initial_risks: Sequence[float], scenarios_list: Sequence[QFDataFrame]) -> QFDataFrame:
        """
        Creates a pandas.DataFrame showing how many strategies failed (reached certain draw down level) and how many
        of them succeeded (that is: reached the target return and not failed on the way).

        Parameters
        ----------
        initial_risks: Sequence[float]
            list of initial_risk parameters where initial_risk is a float number
        scenarios_list: Sequence[pandas.DataFrame]
            list with scenarios (QFDataFrame) where each DataFrame corresponds to one initial_risk value
            Each DataFrame has columns corresponding to different scenarios and its indexed by Trades' ordinal number.
            Its values are returns of Trades.

        Returns
        -------
        pandas.DataFrame
            DataFrame indexed with initial_risk values and with columns FAILED (fraction of scenarios that failed)
            and SUCCEEDED (fraction of scenarios that met the objective and didn't fail on the way)
        """
        result = QFDataFrame(
            index=pd.Index(initial_risks), columns=pd.Index([self.FAILED, self.SUCCEEDED]), dtype=np.float64)

        for init_risk, scenarios in zip(initial_risks, scenarios_list):
            # calculate drawdown for each scenario

            scenarios_df = cast_dataframe(scenarios, SimpleReturnsDataFrame)  # type: SimpleReturnsDataFrame
            max_drawdowns = max_drawdown(scenarios_df)
            total_returns = scenarios_df.total_cumulative_return()

            failed = max_drawdowns >= self._max_accepted_dd
            reached_target_return = total_returns >= self._target_return
            succeeded = ~failed & reached_target_return

            num_of_scenarios = scenarios_df.num_of_columns
            failed_normalized = failed.sum() / num_of_scenarios
            succeeded_normalized = succeeded.sum() / num_of_scenarios

            result.loc[init_risk, [self.FAILED, self.SUCCEEDED]] = [failed_normalized, succeeded_normalized]

        return result
