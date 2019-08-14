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

import matplotlib.pyplot as plt
import pandas as pd

from qf_lib.common.enums.orientation import Orientation
from qf_lib.plotting.charts.bar_chart import BarChart
from qf_lib.plotting.decorators.data_element_decorator import DataElementDecorator
from qf_lib.plotting.helpers.index_translator import IndexTranslator

index = ['constant', 'b', 'c', 'd']
# index = [0, 4, 5, 6]

labels_to_locations_dict = {
    'constant': 0,
    'b': 4,
    'c': 5,
    'd': 6
}

colors = ['orange'] + ['forestgreen'] * 3


def main():
    # using automatic mapping between labels and locations
    bar_chart2 = BarChart(orientation=Orientation.Horizontal, index_translator=IndexTranslator(),
                          thickness=1.0, color=colors, align='center')
    bar_chart2.add_decorator(DataElementDecorator(pd.Series(data=[1, 2, 3, 4], index=index)))
    bar_chart2.add_decorator(DataElementDecorator(pd.Series(data=[3, 1, 2, 4], index=index)))
    bar_chart2.plot()

    # using custom mapping between labels and locations
    bar_chart = BarChart(orientation=Orientation.Horizontal, index_translator=IndexTranslator(labels_to_locations_dict),
                         thickness=1.0, color=colors, align='center')
    bar_chart.add_decorator(DataElementDecorator(pd.Series(data=[1, 2, 3, 4], index=index)))
    bar_chart.add_decorator(DataElementDecorator(pd.Series(data=[3, 1, 2, 4], index=index)))
    bar_chart.plot()

    plt.show(block=True)


if __name__ == '__main__':
    main()
