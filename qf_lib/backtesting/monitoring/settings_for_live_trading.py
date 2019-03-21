from datetime import datetime
from typing import List, Type, Dict

from qf_lib.analysis.timeseries_analysis.timeseries_analysis_dto import TimeseriesAnalysisDTO
from qf_lib.common.tickers.tickers import Ticker
from qf_lib.common.utils.dateutils.date_to_string import date_to_str


class LiveTradingSettings(object):
    def __init__(self, live_start_date: datetime, initial_risk: float, all_tickers: List[Ticker],
                 model_type_tickers_dict: Dict[Type, List[Ticker]], is_tms_analysis: TimeseriesAnalysisDTO, title: str):

        self.live_start_date = live_start_date
        self.initial_risk = initial_risk
        self.all_tickers = all_tickers,
        self.model_type_tickers_dict = model_type_tickers_dict,
        self.is_tms_analysis = is_tms_analysis
        self.title = title

    def __str__(self):
        string = "{}\n" \
                 "\tlive trading date: {}" \
                 "\tinitial risk: {}" \
                 "\tall tickers: {}" \
                 "\tmodel type to tickers dict: {}" \
                 "\tis tms analysis: {}" \
                 "\ttitle: {}".format(self.__class__.__name__, date_to_str(self.live_start_date), self.initial_risk,
                                      self.all_tickers, self.model_type_tickers_dict, self.is_tms_analysis, self.title)
        return string
