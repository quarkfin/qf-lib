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
import pandas as pd


class TimeIndexedContainer:

    def infer_interval(self) -> (pd.Timedelta, float):
        """
        Checks what is the most frequent difference between 2 consecutive dates in the index.

        Returns
        -------
        top_frequent_delta
            the most frequent difference between 2 consecutive dates in the index (if there is more than one top
            frequent difference then all of the top frequent differences will be combined into one by calculating
            the mean of top frequent differences).
        relative_frequency
            relative number of occurrences as number from range (0,1>, where 1 means that 100% of time deltas is equal
            to the top_frequent_deltas, thus all time deltas are the same.

        """
        occurrences_dict = {}
        top_count = 0
        top_frequent_deltas = []

        dates = self.index

        if len(dates) <= 1:
            raise ValueError("Index is too short. It must contain at least 2 values for automatic frequency setting.")

        time_deltas = [dates[i] - dates[i - 1] for i in range(1, len(dates))]

        for item in time_deltas:
            item_count = occurrences_dict.get(item, 0) + 1
            occurrences_dict[item] = item_count
            if item_count == top_count:
                top_frequent_deltas.append(item)
            elif item_count > top_count:
                top_frequent_deltas = [item]
                top_count = item_count

        relative_frequency = top_count / len(time_deltas)

        # if there is more than one delta of top frequency then combine them by calculating the mean
        # "top frequency delta" and assigning the combined_relative_frequency as the combined number of occurrences
        # of all "top frequency deltas".
        top_frequent_delta = pd.Series(data=top_frequent_deltas).mean()
        combined_relative_frequency = len(top_frequent_deltas) * relative_frequency

        return top_frequent_delta, combined_relative_frequency
