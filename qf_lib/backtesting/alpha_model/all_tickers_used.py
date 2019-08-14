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
