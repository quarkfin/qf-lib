from dic.container import Container

from qf_lib.backtesting.contract_to_ticker_conversion.vol_strategy_mapper import VolStrategyContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.events.notifiers import Notifiers
from qf_lib.backtesting.monitoring.live_trading_monitor import LiveTradingMonitor
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.position_sizer.initial_risk_position_sizer import InitialRiskPositionSizer
from qf_lib.backtesting.position_sizer.simple_position_sizer import SimplePositionSizer
from qf_lib.backtesting.trading_session.trading_session import TradingSession
from qf_lib.common.utils.dateutils.timer import RealTimer
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.data_providers.bloomberg import BloombergDataProvider
from qf_lib.interactive_brokers.ib_broker import IBBroker
from qf_lib.settings import Settings


class LiveTradingSession(TradingSession):
    """
    Encapsulates the settings and components for Live Trading
    """

    def __init__(self, trading_session_name: str, container: Container):
        """
        Set up the configuration of all elements.
        """
        super().__init__()
        self.logger = qf_logger.getChild(self.__class__.__name__)
        self.trading_session_name = trading_session_name

        self.settings = container.resolve(Settings)                     # type: Settings
        self.data_provider = container.resolve(BloombergDataProvider)   # type: BloombergDataProvider
        self.pdf_exporter = container.resolve(PDFExporter)              # type: PDFExporter
        self.excel_exporter = container.resolve(ExcelExporter)          # type: ExcelExporter

        self.timer = RealTimer()
        self.data_handler = DataHandler(self.data_provider, self.timer)
        self.monitor = LiveTradingMonitor(self.settings, self.pdf_exporter, self.excel_exporter)
        self.broker = IBBroker()

        self.contract_ticker_mapper = VolStrategyContractTickerMapper()
        self.order_factory = OrderFactory(self.broker, self.data_handler, self.contract_ticker_mapper)
        self.position_sizer = InitialRiskPositionSizer(self.broker, self.data_handler, self.order_factory,
                                                       self.contract_ticker_mapper, initial_risk=0.01)
        self.notifiers = Notifiers(self.timer)

        self.logger.info(
            "\n".join([
                "Creating Backtest Trading Session: ",
                "\tTrading Session Name: {}".format(trading_session_name),
                "\tSettings: {}".format(self.settings.__class__.__name__),
                "\tData Provider: {}".format(self.data_provider.__class__.__name__),
                "\tPDF Exporter: {}".format(self.pdf_exporter.__class__.__name__),
                "\tExcel Exporter: {}".format(self.excel_exporter.__class__.__name__),
                "\tData Handler: {}".format(self.data_handler.__class__.__name__),
                "\tMonitor: {}".format(self.monitor.__class__.__name__),
                "\tBroker: {}".format(self.broker.__class__.__name__),
                "\tContract-Ticker Mapper: {}".format(self.contract_ticker_mapper.__class__.__name__),
                "\tOrder Factory: {}".format(self.order_factory.__class__.__name__),
                "\tPosition Sizer: {}".format(self.position_sizer.__class__.__name__),
                "\tNotifiers: {}".format(self.notifiers.__class__.__name__)
            ])
        )

    def start_trading(self) -> None:
        raise NotImplementedError("This method should not be used in live trading")
