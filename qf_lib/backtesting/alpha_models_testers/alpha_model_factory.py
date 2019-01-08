from typing import Type

from geneva_analytics.backtesting.alpha_models.vol_long_short.vol_long_short import VolLongShort
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.data_handler.data_handler import DataHandler


class AlphaModelFactory(object):
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler

    def make_model(self, model_type: Type[AlphaModel], *params, risk_estimation_factor=None):
        model = model_type(*params, risk_estimation_factor=risk_estimation_factor, data_handler=self.data_handler)
        return model

    def make_parametrized_vol_long_short_model(self):
        params = (4.5, 2, 5)
        risk_param = 1.25
        return VolLongShort(*params, risk_estimation_factor=risk_param, data_handler=self.data_handler)

