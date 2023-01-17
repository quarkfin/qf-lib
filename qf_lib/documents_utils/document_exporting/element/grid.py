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

from typing import List, Optional, Tuple

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.documents_utils.document_exporting import templates
from qf_lib.documents_utils.document_exporting.document import Document
from qf_lib.documents_utils.document_exporting.element import Element
from qf_lib.documents_utils.document_exporting.element.chart import ChartElement
from qf_lib.plotting.charts.chart import Chart


class GridElement(Element):
    def __init__(self, mode: PlottingMode, elements: List[Element] = None, figsize: Tuple[float, float] = None,
                 dpi=250, optimise=False):
        """
        Builds a grid out of a list of ``ChartElement``s.

        In PDF mode the charts will be shown in two columns always.
        In Web mode the charts will use the grid proportions specified in ``add_chart`` or ``ChartElement``.

        Parameters
        ----------
        mode
            Either PDF or Web. Determines whether the grid element is going to be rendered in a PDF or a website.
        elements
            A list of elements to be shown in the grid.
        figsize
            Determines the aspect ratio of the charts. This will only be used for charts added via ``add_chart``.
        dpi
            The dots per inch of the charts. This determines the resolution of the chart. This will only be used for
            charts added via ``add_chart``.
        optimise
            Whether the generated chart image size should be reduced.  This will only be used for
            charts added via ``add_chart``.
        """
        super().__init__()
        if elements is None:
            self._elements = []
        else:
            self._elements = elements

        self.mode = mode
        self.figsize = figsize
        self.dpi = dpi
        self.optimise = optimise

    def generate_html(self, document: Optional[Document] = None) -> str:
        """
        Generates the HTML necessary to display the underlying grid of charts in a PDF. Each ``ChartElement``'s
        ``generate_html`` method is called, this means that charts will be saved during the execution of this
        method in the output directory.
        """
        env = templates.environment

        template = env.get_template("grid.html")
        return template.render(elements=self._elements, document=document, pdf_mode=self.mode == PlottingMode.PDF)

    def generate_data(self):
        return [element.generate_data() for element in self._elements]

    def generate_json(self):
        """
        Iterates through the charts currently added to this grid and gets the base64 encoding of each one.

        Returns
        -------
        An array of base64 images (with the encoding prefix)
        """
        temp = list()
        for element in self._elements:
            temp.append(element.generate_json())
        return temp

    def add_chart(self, chart: Chart, grid_proportion=GridProportion.Eight) -> ChartElement:
        """
        Add a chart to this grid. Plot settings such as ``figsize``, ``dpi`` and ``optimise`` will be based on
        the ones specified to this GridElement's constructor.

        Parameters
        ----------
        chart
        grid_proportion
            The proportion of the grid that this chart should use up (out of 16). As an example, to get 4 charts side
            by side set this to ``4``. This is currently only used in the ``Web`` plotting mode.


        Returns
        -------
        The ChartElement instance that was constructed for this chart.
        """
        result = ChartElement(chart, self.figsize, self.dpi, self.optimise, grid_proportion)
        self._elements.append(result)
        return result

    def add_element(self, element: Element) -> None:
        """
        Add a chart element to this grid.
        """
        self._elements.append(element)
