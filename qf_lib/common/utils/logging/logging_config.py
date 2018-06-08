import logging
import sys
from datetime import datetime
from os import makedirs

from os.path import exists, join

from qf_lib.common.utils.helpers import get_formatted_filename
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.get_sources_root import get_src_root


def setup_logging(level, console_logging=True, log_dir=None, log_file_base_name=None):
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    qf_logger.setLevel(level)

    # config logging to file
    if log_dir is not None:
        abs_log_dir = join(get_src_root(), log_dir)
        log_file = get_formatted_filename(log_file_base_name, datetime.now(), "txt")

        if not exists(abs_log_dir):
            makedirs(abs_log_dir)

        file_handler = logging.FileHandler(join(abs_log_dir, log_file))
        file_handler.setFormatter(formatter)
        qf_logger.addHandler(file_handler)

    # config logging to console (stdout)
    if console_logging:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        qf_logger.addHandler(stream_handler)
