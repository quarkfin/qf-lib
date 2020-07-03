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

import textwrap

from qf_lib.plotting.decorators.chart_decorator import ChartDecorator


class TitleDecorator(ChartDecorator):
    """Adds title to the chart.

    Parameters
    ----------
    title: str
        title that should be added
    key: str
        see: ChartDecorator.__init__#key
    """
    def __init__(self, title: str, key: str = None):
        super().__init__(key)
        self._title = title

    def decorate(self, chart: "Chart") -> None:
        axes = chart.axes

        # Word wrap to 60 characters.
        title = "\n".join(textwrap.wrap(self._title, width=60))

        axes.set_title(title)
