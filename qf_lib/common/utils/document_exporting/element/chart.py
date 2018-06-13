import uuid
from typing import Tuple

from jinja2 import Template

from qf_lib.common.enums.grid_proportion import GridProportion
from qf_lib.common.enums.plotting_mode import PlottingMode
from qf_lib.common.utils.document_exporting import templates
from qf_lib.common.utils.document_exporting.document import Document
from qf_lib.common.utils.document_exporting.element import Element
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.plotting.charts.chart import Chart


class ChartElement(Element):
    def __init__(self, chart: Chart, mode: PlottingMode=PlottingMode.PDF, figsize: Tuple[float, float]=None, dpi=250,
                 optimise=False, grid_proportion=GridProportion.Eight, comment: str=""):
        """
        Constructs a new chart element that can be rendered in a PDF or on a website.

        Parameters
        ----------
        chart
            The chart to wrap inside this element.
        mode
            Either ``PDF`` or ``Web``, determines where this chart element will be rendered.
        figsize
            Determines the size ratio of the chart. This is a width, height tuple specified in inches. For example:
            (13, 5) for a wide and short chart size.
        dpi
            Determines the DPI (Dots per Inch) of the chart (can be used to control the resolution).
        optimise
            Determines whether the file size of the generated chart should be reduced. The reduction is performed by
            recompressing the image using the PIL library, the color space is converted to something more
            space-efficient and PIL is instructed to make the output file as small as possible.
        grid_proportion
            The proportion of the grid that this chart should use up (out of 16).
            As an example, to get 4 charts side by side set this to ``4``. This is currently only used in
            the ``Web`` plotting mode.
        comment
            An optional comment to add underneath a chart shown inside a PDF.
        """
        super().__init__(grid_proportion)
        self._chart = chart
        self._filename = "{}.png".format(uuid.uuid4())
        self.mode = mode
        self.figsize = figsize
        self.dpi = dpi
        self.optimise = optimise
        self.grid_proportion = grid_proportion
        self.comment = comment
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def get_grid_proportion_css_class(self) -> str:
        return str(self.grid_proportion)

    def generate_json(self) -> str:
        """
        Generates the base64 image of the chart. The chart is rendered in
        memory, then encoded to base64.

        Returns
        -------
        A string with the base64 image (with encoding prefix) of the chart.
        """
        try:
            result = "data:image/png;base64," + self._chart.render_as_base64_image(
                self.mode, self.figsize, self.dpi, self.optimise)
        except Exception as ex:
            self.logger.exception('Chart generation error:')
            result = "error: Chart generation error: " + str(ex)
        # Close the chart's figure as we are no longer going to be using it.
        self._chart.close()
        return result

    def generate_html(self, document: Document) -> str:
        """
        Generates the HTML necessary to display the underlying chart in a PDF document. The chart is rendered in
        memory, then encoded to base64 and embedded in the HTML
        """
        try:
            base64 = self._chart.render_as_base64_image(
                self.mode, self.figsize, self.dpi, self.optimise)

            env = templates.environment
            template = env.get_template("chart.html")
            result = template.render(data=base64, width="100%")

        except Exception as ex:
            self.logger.error('Chart generation error:')
            self.logger.error(ex)
            result = "<h2 class='chart-render-failure'>Failed to render chart</h1>"
        # Close the chart's figure as we are no longer going to be using it.
        self._chart.close()
        # Add the optional comment.
        result += self._create_html_comment()

        return result

    def _create_html_comment(self):
        template = Template("""
            <p class="comment">{{ comment }}</p>
        """)

        return template.render(comment=self.comment)
