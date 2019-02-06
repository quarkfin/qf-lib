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
