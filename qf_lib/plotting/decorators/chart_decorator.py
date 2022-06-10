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

import uuid


class ChartDecorator:
    """
    Abstract class for Chart decorators. Decorators are objects which add something to the chart (e.g. to Axes object)
    after the main chart has been plotted. To use a decorator you need to create it first and then add it to the chart
    using the Chart.add_decorator(ChartDecorator) method.

    Parameters
    ----------
    key: str, optional
        Key is the identifier of the decorator. It must be unique to each decorator across the chart. If `None`
        is specified then the unique key is generated automatically.
    """

    def __init__(self, key: str = None):
        if key is None:
            key = str(uuid.uuid4())

        self.key = key

    def decorate(self, chart: "Chart") -> None:
        """
        Modifies the axes object taken from the chart (e.g. adds legend, draws cone, etc.).
        """
        raise NotImplementedError()

    def decorate_html(self, chart: "Chart", chart_id: str) -> str:
        """
        Constructs code to decorate an existing web chart.

        Parameters
        ----------
        chart: Chart
        chart_id: str
            A string identifying the specific chart. For the web, the <div> that represents this chart will typically
            use this as its id.

        Returns
        -------
        str
            JavaScript code that is called before the underlying chart is initialised. The code can modify the pre-defined
            options variable.
        """
        return ""
