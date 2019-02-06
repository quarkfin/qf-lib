from datetime import datetime
from os.path import join
from typing import Sequence, Dict, Type

import pandas as pd
from dic.container import Container

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel
from qf_lib.backtesting.alpha_models_testers.alpha_model_factory import AlphaModelFactory
from qf_lib.backtesting.monitoring.dummy_monitor import DummyMonitor
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.strategy.trading_strategy import TradingStrategy
from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import str_to_ticker, Ticker
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.settings import Settings


class LiveMonitorHelper(object):

    def __init__(self, container: Container, live_start_date: datetime, initial_risk: float,
                 all_tickers: Sequence[Ticker], model_type_tickers_dict: Dict[Type[AlphaModel], Sequence[Ticker]]):
        self.container = container
        self.settings = self.container.resolve(Settings)
        self.live_start_date = live_start_date
        self.end_date = datetime.now()
        self.initial_risk = initial_risk
        self.all_tickers_used = all_tickers

        session_builder = BacktestTradingSessionBuilder(self.live_start_date, self.end_date)
        session_builder.set_position_sizer(InitialRiskPositionSizer, self.initial_risk)
        session_builder.set_monitor_type(DummyMonitor)

        backtest_ts = session_builder.build(self.container)
        backtest_ts.use_data_preloading(self.all_tickers_used)

        self.backtest_ts = backtest_ts
        model_factory = AlphaModelFactory(backtest_ts.data_handler)
        model_tickers_dict = {}
        for model_type, tickers in model_type_tickers_dict.items():
            model = model_factory.make_parametrized_model(model_type)
            model_tickers_dict[model] = tickers
        self.strategy = TradingStrategy(self.backtest_ts, model_tickers_dict)

        self.signals_df = None
        self.exposures_df = None
        self.fractions_at_risk_df = None

    def collect_backtest_result(self):
        self.backtest_ts.start_trading()
        self.signals_df = self.strategy.signals_df
        self.exposures_df = self.signals_df.applymap(lambda x: x.suggested_exposure.name)
        self.fractions_at_risk_df = self.signals_df.applymap(lambda x: x.fraction_at_risk)

        portfolio_tms = self.backtest_ts.portfolio.get_portfolio_timeseries()
        portfolio_tms.index = portfolio_tms.index.date  # remove time part
        self.exposures_df["c/c return"] = portfolio_tms.to_simple_returns()

    def generate_past_signals_file(self):
        # ===== summary export =====
        file_name_template = datetime.now().strftime("%Y_%m_%d-%H%M {}".format('past_signals.xlsx'))
        xlx_file_path = join('past_signals', file_name_template)
        xlx_exporter = ExcelExporter(self.settings)
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

    def generate_cone_chart(self):
        pass








