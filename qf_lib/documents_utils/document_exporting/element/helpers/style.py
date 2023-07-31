from typing import Dict, Sequence, Union, Any

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class Style:
    def __init__(self, style: Dict[str, str] = None, css_class: str = None):
        self.style = style if style is not None else dict()
        self.css_class = css_class.split() if css_class is not None else []
        self.logger = qf_logger.getChild(self.__class__.__name__)

    def add_css_class(self, css_classes: Sequence[str]):
        self.css_class.extend(css_classes)

    def remove_css_class(self, css_classes: Sequence[str]):
        for class_name in css_classes:
            try:
                self.css_class.remove(class_name)
            except ValueError:
                self.logger.warning("The css class {} can not be removed, as it does not exist".format(class_name))

    def add_styles(self, styles_dict: Dict[str, str]):
        styles_dict = {key.replace(" ", ""): value.replace(" ", "") for key, value in styles_dict.items()}
        self.style.update(styles_dict)

    def remove_styles(self, styles: Union[Dict[str, str], Sequence[str]]):
        properties = styles.keys() if type(styles) is dict else styles
        for property_name in properties:
            try:
                del self.style[property_name]
            except KeyError:
                self.logger.warning("The css style for proptyety {} can not be removed, as it does not exist".
                                    format(property_name))

    def styles(self):
        # The function merges into string all styles. This string may be further used as the css styles attributes
        # value. No spaces between attributes and their values are allowed.
        def merge_styles(styles_dict: Dict[str, str]) -> str:
            return "".join(['%s:%s;' % (key, value) for key, value in styles_dict.items()])

        styles = merge_styles(self.style)
        styles = '""' if len(styles) == 0 else styles

        return styles

    def classes(self):
        def merge_classes(css_classes_list: Sequence[str]) -> str:
            return " ".join(css_classes_list)

        css_classes = merge_classes(self.css_class)
        return css_classes


class ColumnStyle(Style):
    def __init__(self, column_name: str, style: Dict[str, str] = None, css_class: str = None):
        super().__init__(style, css_class)
        self.column_name = column_name


class RowStyle(Style):
    def __init__(self, label: Any, style: Dict[str, str] = None, css_class: str = None):
        super().__init__(style, css_class)
        self.label = label


class CellStyle(Style):
    def __init__(self, row_style, column_style, style: Dict[str, str] = None, css_class: str = None):
        super().__init__(style, css_class)
        self.row_style = row_style
        self.column_style = column_style

    def styles(self):
        # The function merges into string all styles, corresponding to the row, column and cell.
        styles = super().styles()

        styles = self.row_style.styles() + self.column_style.styles() + styles
        styles = styles.replace('""', '')
        styles = '""' if len(styles) == 0 else styles

        return styles

    def classes(self):
        # The function merges into string all styles, corresponding to the row, column and cell. This string may be
        # further used as the css class attribute value
        classes = super().classes()

        css_classes = self.row_style.classes() + self.column_style.classes() + classes
        css_classes = css_classes.replace('""', '')
        css_classes = '""' if len(css_classes) == 0 else css_classes

        return css_classes
