from typing import Optional

from os.path import dirname, join, pardir, abspath


def get_src_root() -> Optional[str]:
    """
    Returns an absolute path of the sources root directory ("qf-lib" directory).
    """
    return abspath(join(dirname(__file__), pardir))
