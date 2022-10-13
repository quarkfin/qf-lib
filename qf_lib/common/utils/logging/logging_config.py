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

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.helpers import get_formatted_filename
from qf_lib.common.utils.logging.qf_parent_logger import loggers
from qf_lib.starting_dir import get_starting_dir_abs_path


def setup_logging(level, console_logging=True, log_dir=None, log_file_base_name="", logger_name: str = 'qf'):
    if logger_name not in loggers.keys():
        raise KeyError(f'{logger_name}_logger is not available. Please add it to loggers.')
    _inner_setup_logging(loggers[logger_name], level, console_logging, log_dir, "QF_" + log_file_base_name)


def _inner_setup_logging(logger, level, console_logging, log_dir, log_file_base_name):
    logging.basicConfig(level=level)
    if console_logging:
        add_console_output_handler(logger, level)

    # config logging to file
    if log_dir:
        add_file_handler(logger, level, log_dir, log_file_base_name)


def add_file_handler(logger: logging.Logger, logging_level, log_dir: str, log_file_base_name: Optional[str] = ""):
    """ Adds a FileHandler to the logger instance.

    Important Note: the function only saves the level on the FileHandler, not on the logger. If you set
    your logger to the level WARNING, then adding FileHandler with logging_level = DEBUG will still include
    only logs, which severity is >= WARNING. If you want the DEBUG logs to be tracked by the FileHandler
    call on your logger object: logger.setLevel(logging.DEBUG).

    Parameters
    -----------
    logger: logging.Logger
        logger instance
    logging_level:
        minimum logging level, above which all logs will be tracked by the FileHandler and saved to the
        txt file
    log_dir: str
        directory in which all the log files should be stored
    log_file_base_name: str
        base name of the file. All log files will be of the form "<current time>_<log_file_base_name>.txt"
    """
    abs_log_dir = Path(get_starting_dir_abs_path()) / log_dir
    abs_log_dir.mkdir(parents=True, exist_ok=True)

    log_file = get_formatted_filename(log_file_base_name, datetime.now(), "txt")

    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        datefmt=str(DateFormat.ISO_SECONDS)
    )

    # If not already exists a FileHandler, add one
    if not any(isinstance(handle, logging.FileHandler) for handle in logger.handlers):
        file_logger = logging.FileHandler(abs_log_dir / log_file)
        file_logger.setFormatter(formatter)
        file_logger.setLevel(logging_level)
        logger.addHandler(file_logger)
        logger.propagate = False


def add_console_output_handler(logger: logging.Logger, logging_level):
    """ Adds a StreamHandler to the logger instance, which will print all the logs to the console output.

    Important Note: the function only saves the level on the FileHandler, not on the logger. If you set
    your logger to the level WARNING, then adding this handler with logging_level = DEBUG will still include
    only logs, which severity is >= WARNING. If you want the DEBUG logs to be tracked by the FileHandler
    call on your logger object: logger.setLevel(logging.DEBUG).

    Parameters
    -----------
    logger: logging.Logger
        logger instance
    logging_level:
        minimum logging level, above which all logs will be printed out in the console
    """
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        datefmt=str(DateFormat.ISO_SECONDS)
    )

    # If not already exists a streamhandler, add one
    if not any(isinstance(handle, logging.StreamHandler) for handle in logger.handlers):
        # config logging to console (stdout)
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging_level)
        logger.addHandler(stream_handler)
