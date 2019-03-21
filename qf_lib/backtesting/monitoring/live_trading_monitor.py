from datetime import datetime
from typing import List

from dic.container import Container

from qf_lib.analysis.strategy_monitoring.live_trading_sheet import LiveTradingSheet
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.events.time_event.after_market_close_event import AfterMarketCloseEvent
from qf_lib.backtesting.monitoring.dummy_monitor import DummyMonitor
from qf_lib.backtesting.monitoring.past_signals_generator import PastSignalsGenerator
from qf_lib.backtesting.monitoring.settings_for_live_trading import LiveTradingSettings
from qf_lib.common.utils.dateutils.date_to_string import date_to_str
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.publishers.email_publishing.email_publisher import EmailPublisher
from qf_lib.settings import Settings


class LiveTradingMonitor(DummyMonitor):
    """
    This Monitor will be used to monitor live trading activities
    """

    def __init__(self, notifiers: Notifiers, container: Container, settings_for_live_trading: LiveTradingSettings):
        self.notifiers = notifiers
        self.container = container
        self.trading_settings = settings_for_live_trading
        self.notifiers.scheduler.subscribe(AfterMarketCloseEvent, listener=self)

    def on_after_market_close(self, after_close_event: AfterMarketCloseEvent):
        self.end_of_day_update()

    def end_of_day_update(self, timestamp: datetime = None):
        """
        Generate daily pdf with backtest monitoring and past signals excel file and sends it by email
        """
        attachments_paths = self._generate_files()
        self._publish_by_email(attachments_paths, timestamp)

    def _generate_files(self):
        signal_generator = PastSignalsGenerator(container=self.container,
                                                live_start_date=self.trading_settings.live_start_date,
                                                initial_risk=self.trading_settings.initial_risk,
                                                all_tickers=self.trading_settings.all_tickers,
                                                model_type_tickers_dict=self.trading_settings.model_type_tickers_dict)
        signal_generator.collect_backtest_result()
        past_signals_file_path = signal_generator.generate_past_signals_file()

        live_trading_sheet = LiveTradingSheet(settings=self.container.resolve(Settings),
                                              pdf_exporter=self.container.resolve(PDFExporter),
                                              strategy_tms=signal_generator.backtest_tms,
                                              strategy_leverage_tms=signal_generator.leverage_tms,
                                              is_tms_analysis=self.trading_settings.is_tms_analysis,
                                              title=self.trading_settings.title)

        live_trading_sheet.build_document()
        live_trading_sheet_path = live_trading_sheet.save()

        return [past_signals_file_path, live_trading_sheet_path]

    def _publish_by_email(self, attachments_dirs: List[str], timestamp):

        class EmailUser(object):
            def __init__(self, name, email_address):
                self.name = name
                self.email_address = email_address

        date_str = date_to_str(timestamp.date())
        template_path = 'live_trading_report.html'

        users = {
            EmailUser("Marcin", "marcin.borratynski@cern.ch"),
            # EmailUser("Olga", "olga.kalinowska@cern.ch"),
        }

        email_publisher = self.container.resolve(EmailPublisher)

        for user in users:
            email_publisher.publish(
                mail_to=user.email_address,
                subject="Live Trading Summary: " + date_str,
                template_path=template_path,
                attachments=attachments_dirs,
                context={'user': user, 'date': date_str}
            )

