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
import itertools
from typing import List, Tuple, Callable, Optional
import pandas as pd
import numpy as np

from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.utils.returns.cagr import cagr
from qf_lib.containers.dataframe.qf_dataframe import QFDataFrame
from qf_lib.containers.dataframe.simple_returns_dataframe import SimpleReturnsDataFrame
from qf_lib.containers.series.qf_series import QFSeries


class OverfittingAnalysis:
    """
    Class providing statistics and analysis for checking if backtest is overfitted.
    It is based on the algorithms described in "The probability of backtest overfitting" by Bailey,
    Borwein, Lopez de Prado and Jim Zhu.
    """

    def __init__(self, multiple_returns_timeseries: SimpleReturnsDataFrame, ranking_function: Callable,
                 num_of_slices: int = 14):

        self.num_of_slices = num_of_slices
        assert self.num_of_slices % 2 == 0, "Number of slices should be an even number"

        self.ranking_function = ranking_function
        self.multiple_returns_timeseries = multiple_returns_timeseries

        self._is_set = None
        self._oos_set = None
        """ Cell matrices with 2 columns and multiple rows. In each cell there is a multiple timeseries
        (dates column + one column of returns for each strategy). First column contains In-Sample sets
        and the second one contains Out-Of-Sample sets. """

        self.is_ranking = None  # type: Optional[List[QFDataFrame]]
        """ List of QFDataFrames, each of which contains 2 columns - quality and rank, and is indexed by the strategies
        names. Looking at one of these data frames we can learn which strategy (described using its name) had the
        highest performance ("rank") and what was that performance ("quality") in the In-Sample period. """

        self.oos_ranking = None  # type: Optional[List[QFDataFrame]]
        """ List of QFDataFrames, each of which contains 2 columns - quality and rank, and is indexed by the strategies
        names. Looking at one of these data frames we can learn which strategy (described using its name) had the
        highest performance ("rank") and what was that performance ("quality") in the Out-Of-Sample period. """

        self.best_is_strategies_names = None  # Optional[List[str]]
        """ List of strategies with the maximum rank. If multiple values equal the maximum, the first strategy with
        that rank is returned. """

        self._rankings_computed = False

    def calculate_overfitting_probability(self):
        """ Returns the probability of backtest overfitting. """
        if not all([self.best_is_strategies_names, self.oos_ranking, self.is_ranking]):
            self.create_is_oos_rankings()

        logits = self.calculate_relative_rank_logits(self.best_is_strategies_names)
        logits_distribution = self._calculate_distribution(logits)
        pbo = logits_distribution.where(logits_distribution.index <= 0).dropna().sum()
        return pbo

    def calculate_probability_of_loss(self):
        """ Returns the probability of loss for the best strategy. """
        self.create_is_oos_rankings()
        best_strategies_annualised_returns = self._get_best_strategies_returns()
        losing_strategies_returns = [returns for returns in best_strategies_annualised_returns if returns < 0]
        pol = len(losing_strategies_returns) / len(best_strategies_annualised_returns)
        return pol

    def calculate_expected_return(self):
        """ Returns the expected return of best strategies in the Out-Of-Sample."""
        self.create_is_oos_rankings()
        best_strategies_annualised_returns = self._get_best_strategies_returns()
        expected_return = sum(best_strategies_annualised_returns) / len(best_strategies_annualised_returns)
        return expected_return

    def get_best_strategies_is_oos_qualities(self):
        """
        Returns
        -------
        QFDataFrame
            dataframe with two columns: OOS and IS, each row contains the quality value of the best IS strategy for both
            in sample (quality of the best strategy) nad out of sample (quality of the strategy that was in this
            combination set, the best one in the in-sample period).
        """
        self.create_is_oos_rankings()
        oos_qualities = [oos_ranking["quality"].loc[best_is_strategy] for oos_ranking, best_is_strategy
                         in zip(self.oos_ranking, self.best_is_strategies_names)]
        is_qualities = [is_ranking["quality"].loc[best_is_strategy] for is_ranking, best_is_strategy
                        in zip(self.is_ranking, self.best_is_strategies_names)]
        return QFDataFrame(data={"OOS": oos_qualities, "IS": is_qualities})

    def calculate_relative_rank_logits(self, strategies_names: List):
        """
        Computes relative ranks for the strategies named in the strategies_names list and afterwards
        calculates the logits. High logit values imply a consistency between IS and OOS performances,
        which indicates a low lever of backtest overfitting.
        """
        self.create_is_oos_rankings()
        num_of_strategies = len(self.multiple_returns_timeseries.columns)
        relative_ranks = QFSeries(data=[oos_ranking["rank"].loc[best_is_strategy] / (num_of_strategies + 1)
                                        for oos_ranking, best_is_strategy in zip(self.oos_ranking, strategies_names)])
        logits = np.log(relative_ranks.divide(1.0 - relative_ranks))
        return logits

    def create_is_oos_rankings(self):
        if not self._rankings_computed:
            self._is_set, self._oos_set = self.form_different_is_and_oos_sets(self.multiple_returns_timeseries)
            self.is_ranking = [self.rank_strategies(is_element) for is_element in self._is_set]
            self.oos_ranking = [self.rank_strategies(oos_element) for oos_element in self._oos_set]

            self.best_is_strategies_names = [is_element["rank"].idxmax() for is_element in self.is_ranking]
            self._rankings_computed = True

    def form_different_is_and_oos_sets(self, multiple_returns_timeseries: QFDataFrame) -> Tuple:
        """
        Splits slices into two groups of equal sizes for all possible combinations.

        Returns an list of tuples. 1st element of the tuple contains the In-Sample set and the 2nd one contains the
        Out-Of-Sample set (both in form of QFDataFrames). Each tuple contains one of possible combinations
        of slices forming IS and OOS sets. E.g. if there are 4 slices: A,B,C,D then one of possible
        combinations is IS: A,B and OOS: C,D. The given example will be one of rows of the result list.
        A and B (C and D) will be concatenated (so that there will be one timeseries AB),
        and so will be one CD timeseries.
        """
        # Drop all rows not aligned to num_of_slices. E.g if the df has 233 rows and the num_of_slices is 50,
        # then last 33 rows of the original matrix will be dropped
        rows_to_keep = (multiple_returns_timeseries.num_of_rows // self.num_of_slices) * self.num_of_slices
        aligned_df = multiple_returns_timeseries.iloc[:rows_to_keep]
        if aligned_df.empty:
            raise ValueError("Too few rows in the data frame.")

        size_of_slices = aligned_df.num_of_rows // self.num_of_slices
        df_slices = [SimpleReturnsDataFrame(aligned_df.iloc[i:i + size_of_slices, :])
                     for i in range(0, len(aligned_df), size_of_slices)]

        # The index order of the original data frame should be preserved in both IS and OOS dfs
        new_index = aligned_df.index[:len(aligned_df) // 2]
        is_dfs = [pd.concat(slices) for slices in itertools.combinations(df_slices, self.num_of_slices // 2)]
        oos_dfs = [aligned_df.loc[aligned_df.index.difference(df.index)] for df in is_dfs]

        # Adjust the indices at the end, after the oos_dfs and is_dfs are already computed
        for df in itertools.chain(is_dfs, oos_dfs):
            df.index = new_index

        return is_dfs, oos_dfs

    def rank_strategies(self, df: SimpleReturnsDataFrame, ascending: bool = True) -> QFDataFrame:
        """
        Rank strategies using the ranking function. The worst strategy should be marked as 1.
        Parameters
        ----------
        df: SimpleReturnsDataFrame
            dataframe containing different strategies returns in the columns
        ascending: bool
            if True - the smaller the measure, the worse is the strategy

        Returns
        -------
        QFDataFrame
            data frame indexed by strategy names with two columns: quality (containing the quality measure
            computed for the given strategy, e.g. sharpe ratio) and rank.

        """
        rank_df = QFDataFrame(data={"quality": [self.ranking_function(df[col]) for col in df.columns]},
                              index=df.columns)

        rank_df = rank_df.replace([np.inf, -np.inf], np.nan)
        if rank_df.isna().values.any():
            raise ValueError("There exist nan or infinite values in the rank_df")
        rank_df["rank"] = rank_df["quality"].rank(method="min", ascending=ascending)
        return rank_df

    def _get_best_strategies_returns(self) -> List[float]:
        """ Returns the annual returns of the best IS strategies """
        annual_returns = []
        for oos_set, best_strategy_name in zip(self._oos_set, self.best_is_strategies_names):
            best_strategy_tms = oos_set.loc[:, best_strategy_name]
            annual_simple_return = cagr(best_strategy_tms, Frequency.DAILY)
            annual_returns.append(annual_simple_return)
        return annual_returns

    def _calculate_distribution(self, qf_series: QFSeries):
        """
        Takes a QFSeries and counts the number occurrences of each value. Then all the occurrences are
        normalized so that they all sum up to one.

        Returns
        --------
        QFSeries
            series, indexed with the values from the original series, containing the normalized numbers of
            occurrences of each of the values

        """
        occurrences = qf_series.value_counts(sort=False).sort_index()
        normalized_occurrences = occurrences / occurrences.sum()
        return normalized_occurrences
