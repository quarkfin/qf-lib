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

import os
import shutil
from unittest import TestCase

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class TestCaseWithFileOutput(TestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self._logger = qf_logger.getChild(self.__class__.__name__)

    def templates_dir(self):
        raise NotImplementedError()

    def tmp_dir(self):
        raise NotImplementedError()

    def template_file_path(self, file_name):
        return os.path.join(self.templates_dir(), file_name)

    def tmp_file_path(self, file_name):
        return os.path.join(self.tmp_dir(), file_name)

    def copy_template_to_tmp(self, file_name):
        template_path = self.template_file_path(file_name)
        file_to_modify_path = self.tmp_file_path(file_name)
        shutil.copyfile(template_path, file_to_modify_path)

        return file_to_modify_path

    def clear_tmp_dir(self):
        try:
            for file in os.listdir(self.tmp_dir()):
                file_path = os.path.join(self.tmp_dir(), file)
                if os.path.isfile(file_path) and os.path.basename(file_path) != '.gitignore':
                    os.unlink(file_path)

        except OSError:
            self._logger.error('Did not manage remove files from tmp directory after running the test')
