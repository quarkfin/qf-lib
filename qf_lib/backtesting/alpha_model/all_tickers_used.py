from typing import Dict, Type, List

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.common.tickers.tickers import Ticker


def get_all_tickers_used(model_type_tickers_dict: Dict[Type[AlphaModel], List[Ticker]]):
    all_tickers = []
    for model_type, traded_tickers_list in model_type_tickers_dict.items():
        non_traded_tickers = list(model_type.settings.tickers_dict.values())
        all_tickers = all_tickers + traded_tickers_list + non_traded_tickers
    result_list = list(set(all_tickers))  # remove potential duplicates
    return result_list
