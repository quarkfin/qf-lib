from datetime import datetime
from typing import List, Type, Dict

from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.returns.is_return_stats import InSampleReturnStats


class LiveTradingSettings(object):
    def __init__(self, live_start_date: datetime, initial_risk: float,
                 model_type_tickers_dict: Dict[Type, List[Ticker]], is_returns_stats: InSampleReturnStats, title: str):
        self.live_start_date = live_start_date
        self.initial_risk = initial_risk
        self.model_type_tickers_dict = model_type_tickers_dict
        self.is_returns_stats = is_returns_stats
        self.title = title

    def __str__(self):
        string = "{}\n" \
                 "\tlive trading date: {}" \
                 "\tinitial risk: {}" \
                 "\tmodel type to tickers dict: {}" \
                 "\tin sample returns statistics: {}" \
                 "\ttitle: {}".format(self.__class__.__name__, date_to_str(self.live_start_date), self.initial_risk,
                                      self.model_type_tickers_dict, self.is_returns_stats, self.title)
        return string
