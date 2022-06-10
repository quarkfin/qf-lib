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

qf_logger = logging.getLogger("qf")

ib_logger = logging.getLogger("ib")

loggers = {'qf': qf_logger, 'ib': ib_logger}

"""
This is the preferred way of using logger in the project. All loggers are the children of QF and therefore
can be filtered in the logging settings.

Usage:

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger

Now in the class you can call
    self.logger = qf_logger.getChild(self.__class__.__name__)
which will create an instance of a logger.

"""
