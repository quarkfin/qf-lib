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

from typing import Type

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.data_handler.data_handler import DataHandler


class AlphaModelFactory(object):
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler

    def make_model(self, model_type: Type[AlphaModel], *params, risk_estimation_factor=None):
        model = model_type(*params, risk_estimation_factor=risk_estimation_factor, data_handler=self.data_handler)
        return model

    def make_parametrized_model(self, model_type: Type[AlphaModel]):
        model = model_type(*model_type.settings.parameters,
                           risk_estimation_factor=model_type.settings.risk_estimation_factor,
                           data_handler=self.data_handler)
        return model
