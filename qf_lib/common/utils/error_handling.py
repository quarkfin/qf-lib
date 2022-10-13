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
import inspect
import traceback

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class ErrorHandling:
    _error_messages = []

    @classmethod
    def error_logging(cls, func):
        """
        Helper function, used to decorate a function, in order to facilitate error handling, which logs the error
        message and records the encountered error. All these errors can be easily printed afterwards.
        """
        logger = qf_logger.getChild(__class__.__name__)

        def wrapped_function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_message = "{}: An error occurred while processing the function {}.\n {}".format(
                    e.__class__.__name__, func.__name__, traceback.format_exc())
                logger.error(error_message)
                cls._error_messages.append(error_message)

        return wrapped_function

    @classmethod
    def class_error_logging(cls):
        """
        Setup error logging for all the functions inside a certain class (including the functions inherited its parent
        classes).
        """

        def wrap(wrapped_cls):
            for function_name, function in inspect.getmembers(wrapped_cls, inspect.isfunction):
                setattr(wrapped_cls, function_name, cls.error_logging(function))
            return wrapped_cls

        return wrap

    @classmethod
    def get_error_messages(cls):
        """
        Method used to get the error messages

        Returns
        -------
        List
            current messages that are stored in the class
        """
        return cls._error_messages

    @classmethod
    def reset_error_messages(cls):
        """
        Method used to reset the error messages to their initial value and return old messages

        Returns
        -------
        List
            old messages that were stored in class
        """
        old_messages = cls._error_messages
        cls._error_messages = []
        return old_messages
