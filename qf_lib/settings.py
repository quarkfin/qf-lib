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

import json
import os
import os.path
from json import JSONDecodeError
from typing import Optional

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class Settings:
    def __init__(self, settings_path: Optional[str] = None, secret_path: Optional[str] = None,
                 init_properties: bool = True):
        self.settings_path = settings_path
        self.secret_path = secret_path
        self.init_properties = init_properties
        self.logger = qf_logger.getChild(self.__class__.__name__)

        if init_properties:
            self._init_settings()

    def _init_settings(self):
        merged_config = self._load_config_dict()
        self._add_settings(self, merged_config)

    def _add_settings(self, settings, items):
        for key in items:
            if type(items[key]) is dict:
                sub_obj = Settings(None, None, init_properties=False)
                self._add_settings(sub_obj, items[key])
                items[key] = sub_obj
            setattr(settings, key, items[key])

    def _load_config_dict(self):
        try:
            self.logger.info(f"Loading settings from file {self.settings_path}")
            with open(self.settings_path, 'r') as file:
                public_settings = json.load(file)
        except (JSONDecodeError, TypeError, FileNotFoundError):
            self.logger.warning(f"The settings file {self.settings_path} is empty or cannot be read")
            public_settings = {}

        if self.secret_path is not None and os.path.isfile(self.secret_path):
            self.logger.info(f"Using secret settings file {self.settings_path}")
            try:
                with open(self.secret_path, 'r') as file:
                    secret_settings = json.load(file)
            except (JSONDecodeError, TypeError, FileNotFoundError):
                self.logger.warning(f"The settings file {self.settings_path} is empty or cannot be read")
                secret_settings = {}
        elif 'QUANTFIN_SECRET' in os.environ:
            self.logger.info("Using QUANTFIN_SECRET env variable")
            try:
                secret_settings = json.loads(os.environ['QUANTFIN_SECRET'])
            except JSONDecodeError:
                self.logger.warning("QUANTFIN_SECRET is empty or cannot be read")
                secret_settings = {}
        else:
            secret_settings = {}
            self.logger.info("No secret settings were defined. Using empty secret settings by default. If needed, "
                             "set the QUANTFIN_SECRET environment variable or get the secret_settings.json file.")

        return self._merge(public_settings, secret_settings)

    def _merge(self, merged_config, config):
        if isinstance(merged_config, dict) and isinstance(config, dict):
            self._merge_dicts(merged_config, config)
        elif isinstance(merged_config, (list, tuple)) and isinstance(config, (list, tuple)):
            merged_config += config
        else:
            raise ValueError("Cannot merge values: {} and {}".format(merged_config, config))

        return merged_config

    def _merge_dicts(self, merged_dict, another_dict):
        for key, value in another_dict.items():
            if key not in merged_dict:
                merged_dict[key] = value
            else:
                merged_dict[key] = self._merge(merged_dict[key], value)

    def __str__(self):
        return "Settings: \n" \
               "\t settings path: {}\n" \
               "\t secret path: {}\n" \
               "\t init properties: {}".format(self.settings_path, self.secret_path, self.init_properties)
