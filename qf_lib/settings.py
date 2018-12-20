import json
import os
from typing import Optional

import os.path

from qf_lib.common.utils.logging.qf_parent_logger import qf_logger


class Settings(object):
    def __init__(self, settings_path: Optional[str], secret_path: Optional[str]=None, init_properties=True):
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
        with open(self.settings_path, 'r') as file:
            public_settings = json.load(file)
        
        if self.secret_path is not None and os.path.isfile(self.secret_path):
            with open(self.secret_path, 'r') as file:
                secret_settings = json.load(file)
            self.logger.info("Using secret_settings.json")
        elif 'QUANTFIN_SECRET' in os.environ:
            secret_settings = json.loads(os.environ['QUANTFIN_SECRET'])
            self.logger.info("Using QUANTFIN_SECRET")
        else:
            raise AttributeError(
                "No secret settings were defined. Either set the QUANTFIN_SECRET environment"
                " variable or get the secret_settings.json file.")

        return self._merge(public_settings, secret_settings)

    def _merge(self, merged_config, config):
        if isinstance(merged_config, dict) and isinstance(config, dict):
            self._merge_dicts(merged_config, config)
        elif isinstance(merged_config, (list, tuple)) and isinstance(config, (list, tuple)):
            merged_config += config
        else:
            raise ValueError(
                "Cannot merge values: {} and {}".format(merged_config, config))

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
