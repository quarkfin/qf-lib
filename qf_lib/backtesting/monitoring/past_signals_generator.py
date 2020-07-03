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

from datetime import datetime
from os.path import join
from typing import Dict, Type, List

import pandas as pd
from dic.container import Container

from qf_lib.backtesting.alpha_model.all_tickers_used import get_all_tickers_used
from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_model.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.alpha_model.alpha_model_strategy import AlphaModelStrategy
from qf_lib.backtesting.monitoring.dummy_monitor import DummyMonitor
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import str_to_ticker, Ticker
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter


class PastSignalsGenerator(object):
    """Class which generated all the previous signals.

    Parameters
    ----------
    container
        container with utils like PDF Generator, Excel Generator and others
    live_start_date
        date from which we will recalculate all the signals
    initial_risk
        value of initial risk for all the models
    model_type_tickers_dict
        dict of model type -> tickers traded by the model
    """

    def __init__(self, container: Container, live_start_date: datetime, initial_risk: float,
                 model_type_tickers_dict: Dict[Type[AlphaModel], List[Ticker]]):
        self.container = container
        self.live_start_date = live_start_date
        self.end_date = datetime.now()
        self.initial_risk = initial_risk
        self.model_type_tickers_dict = model_type_tickers_dict
        self.strategy = self._set_up_trading_strategy(model_type_tickers_dict)

        self.signals_df = None
        self.exposures_df = None
        self.fractions_at_risk_df = None
        self.backtest_tms = None
        self.leverage_tms = None

    def collect_backtest_result(self):
        self.backtest_ts.start_trading()
        self.signals_df = self.strategy.get_signals()
        self.exposures_df = self.signals_df.applymap(lambda x: x.suggested_exposure.name)
        self.fractions_at_risk_df = self.signals_df.applymap(lambda x: x.fraction_at_risk)

        portfolio_tms = self.backtest_ts.portfolio.portfolio_eod_series()
        portfolio_tms.index = portfolio_tms.index.date  # remove time part
        self.backtest_tms = portfolio_tms
        self.exposures_df["c/c return"] = portfolio_tms.to_simple_returns()

        leverage_tms = self.backtest_ts.portfolio.leverage_series()
        leverage_tms.index = leverage_tms.index.date  # remove time part
        self.leverage_tms = leverage_tms
        self.exposures_df["leverage"] = leverage_tms

    def generate_past_signals_file(self):
        # ===== summary export =====
        file_name_template = datetime.now().strftime("%Y_%m_%d-%H%M {}".format('past_signals.xlsx'))
        xlx_file_path = join('past_signals', file_name_template)
        xlx_exporter = self.container.resolve(ExcelExporter)
        path = xlx_exporter.export_container(self.exposures_df, xlx_file_path, include_column_names=True)

        # ===== detailed data collection and export =====
        def unwrap_col_name(column_name: str):
            # returns a tuple (ticker as str extracted form column name, column name)
            return str_to_ticker(column_name.split('@')[0]), column_name

        tickers_columns_list = [unwrap_col_name(column_name) for column_name in self.signals_df]
        fields = [PriceField.Open, PriceField.High, PriceField.Low, PriceField.Close]

        for ticker, column in tickers_columns_list:
            prices_df = self.backtest_ts.data_handler.get_price(ticker, fields, self.live_start_date, self.end_date)
            prices_df = prices_df.reindex(pd.date_range(start=self.live_start_date, end=self.end_date, freq='D'))

            exposure = self.exposures_df[column]
            fraction_at_risk = self.fractions_at_risk_df[column]
            df = pd.concat([prices_df, exposure, fraction_at_risk], axis=1)
            df.columns = ['open', 'high', 'low', 'close', 'exposure', 'fraction_at_risk']
            df.index = exposure.index

            xlx_exporter.export_container(df, xlx_file_path, include_column_names=True, sheet_name=column)
        return path

    def _set_up_trading_strategy(self, model_type_tickers_dict):
        # the settings below should match exactly the setting of the live trading observed
        session_builder = self.container.resolve(BacktestTradingSessionBuilder)
        session_builder.set_position_sizer(InitialRiskPositionSizer, self.initial_risk)
        session_builder.set_monitor_type(DummyMonitor)
        backtest_ts = session_builder.build(self.live_start_date, self.end_date)

        all_tickers = get_all_tickers_used(self.model_type_tickers_dict)
        backtest_ts.use_data_preloading(all_tickers)
        self.backtest_ts = backtest_ts

        model_factory = AlphaModelFactory(backtest_ts.data_handler)
        model_tickers_dict = {}
        for model_type, tickers in model_type_tickers_dict.items():
            model = model_factory.make_parametrized_model(model_type)
            model_tickers_dict[model] = tickers

        strategy = AlphaModelStrategy(self.backtest_ts, model_tickers_dict)
        return strategy
