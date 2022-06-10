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

from numbers import Number
from typing import Mapping, List, Sequence, Union

from qf_lib.common.enums.orientation import Orientation


class IndexTranslator:
    """
    Object which automatically translates label-indexed data into number-indexed data.

    Parameters
    ----------
    labels_to_locations_dict: Mapping[str, Number]
        Contains a mapping from labels to numbers (used as index values for plotting). Must have unique keys
        and unique values.
    """

    def __init__(self, labels_to_locations_dict: Mapping[str, Number] = None):
        self._labels_to_locations_dict = dict()

        if labels_to_locations_dict is not None:
            self._labels_to_locations_dict.update(labels_to_locations_dict)

    @classmethod
    def setup_ticks_and_labels(cls, chart: "Chart"):
        """
        Setups ticks' locations and labels in the given chart if it used IndexTranslator.
        """
        if chart.index_translator is not None:
            index_axis = chart.axes.xaxis if chart._orientation == Orientation.Vertical else chart.axes.yaxis

            ticks = chart.index_translator.values()
            index_axis.set_ticks(ticks)

            labels = chart.index_translator.inv_translate(index_axis.get_ticklocs())
            index_axis.set_ticklabels(labels)

    def translate(self, values: Union[str, Sequence[str]]) -> List[Number]:
        """
        Translates label into numeric coordinate. If the translation is done for the first time for this value
        it may modify the state of the translator (it may introduce a new translation).

        Parameters
        ----------
        values
            values to be translated (e.g. ["SPY", "GOOGL"])

        Returns
        -------
        translated values
            value translated into numeric coordinate
        """
        if isinstance(values, str):
            values = [values]

        result = []
        for value in values:
            if value in self._labels_to_locations_dict:
                numeric_coordinate = self._labels_to_locations_dict[value]
            else:
                numeric_coordinate = self._translate_and_update_dict(value)
            result.append(numeric_coordinate)

        return result

    def inv_translate(self, translated_values: Union[Number, Sequence[Number]]) -> List[str]:
        """
        Translates numeric coordinate into label. Requirement: the Translator must be familiar with mapping the label
        into numeric coordinate (either the translate must have been called or the labels_to_locations_dict must
        contain a proper entry).

        Parameters
        ----------
        translated_values
            numeric values to be changed into labels (e.g. [0.0, 1.0, 2.0])

        Returns
        -------
        labels
            labels corresponding to numeric values
        """
        if isinstance(translated_values, float):
            translated_values = [translated_values]

        inv_dict = {value: key for key, value in self._labels_to_locations_dict.items()}
        return [inv_dict.get(numeric_value, '') for numeric_value in translated_values]

    def values(self) -> List[float]:
        return list(self._labels_to_locations_dict.values())

    def _translate_and_update_dict(self, new_value: str) -> Number:
        first_tick_position = 1.0
        numeric_coordinate = first_tick_position + len(self._labels_to_locations_dict)

        self._labels_to_locations_dict[new_value] = numeric_coordinate
        return numeric_coordinate
