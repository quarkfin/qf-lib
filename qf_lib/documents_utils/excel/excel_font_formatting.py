from enum import Enum
from openpyxl.styles import Font


class ExcelFontMode(Enum):
    """
    Class defining the excel formatting modes.
    """

    NORMAL = 0  # Without any font formatting
    BOLD = 1  # Format the font to bold
    ITALIC = 2  # Format the font to italic
    UNDERLINE = 3  # Format the font to have underline


def change_cell_font_style(cell, font_style: ExcelFontMode, font_size: int = None):
    bold = False
    italic = False
    outline = False

    font_size = font_size or cell.font.size

    if font_style == ExcelFontMode.NORMAL:
        bold = False
        italic = False
        outline = False
    elif font_style == ExcelFontMode.BOLD:
        bold = True
    elif font_style == ExcelFontMode.ITALIC:
        italic = True
    elif font_style == ExcelFontMode.UNDERLINE:
        outline = True

    return Font(color=cell.font.color, name=cell.font.name,
                bold=bold, italic=italic, outline=outline, size=font_size)
