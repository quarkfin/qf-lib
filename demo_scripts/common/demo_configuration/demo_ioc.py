from os.path import join, dirname, abspath


def _get_ioc_container():
    """
    Creates and returns the IoC container. If it already exists the existing instance is returned.

    WARNING: Container shall be used explicitly only in the scripts and NOWHERE ELSE!!! You better don't try to violate
    this rule or I'll find you.
    """
    from dic.container import ContainerBuilder
    from dic.scope import SingleInstance

    # from cern_analytics.data_providers.current_sensitivities_dao import CurrentSensitivitiesDAO
    # from cern_analytics.data_providers.daily_report_dao import DailyReportDAO
    # from cern_analytics.data_providers.db_connection_provider import ReadOnlyDBConnectionProvider
    # from cern_analytics.data_providers.db_connection_provider import ReadWriteDBConnectionProvider
    # from cern_analytics.data_providers.ststmunich_position_dao import StStMunichPositionDAO
    # from cern_analytics.data_providers.true_view.detailed_risk_report_dao import DetailedRiskReportDAO
    # from cern_analytics.data_providers.true_view.trueview_monthly_scenarios_dao import TrueViewMonthlyScenariosDAO
    # from cern_analytics.history_simulation.fund_history_simulator import FundHistorySimulator
    # from cern_analytics.report_generators.sensitivities_report.report_data_downloader import \
    #     SensitivityReportDataDownloader
    # from cern_analytics.report_generators.sensitivities_report.report_database_exporter import \
    #     SensitivitiesDatabaseExporter
    # from cern_analytics.report_generators.sensitivities_report.report_factory import SensitivitiesReportFactory
    # from cern_analytics.report_generators.sensitivities_report.report_pdf_exporter import SensitivitiesPDFExporter
    # from cern_analytics.report_generators.sensitivities_report.subreport_factory.subreport_factory import \
    #     SensitivitiesSubreportFactory
    # from cern_analytics.utils.convexity_periods_calculator import ConvexityPeriodsCalculator
    # from geneva_analytics.data_providers.timeseries_data_provider import TimeseriesDataProvider
    # from qf_lib.common.risk_parity_boxes.risk_parity_boxes import RiskParityBoxesFactory
    # from qf_lib.common.rolling_contracts.rolling_contracts_series_producer import RollingContractsSeriesProducer
    # from qf_lib.common.utils.dateutils.timer import RealTimer
    # from qf_lib.common.utils.dateutils.timer import Timer
    from qf_lib.common.utils.document_exporting.html_exporter import HTMLExporter
    from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
    from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
    from qf_lib.common.utils.excel.excel_importer import ExcelImporter
    from qf_lib.data_providers.bloomberg import BloombergDataProvider
    # from qf_lib.data_providers.cryptocurrency.cryptocurrency_data_provider import CryptoCurrencyDataProvider
    from qf_lib.data_providers.general_price_provider import GeneralPriceProvider
    # from qf_lib.data_providers.haver import HaverDataProvider
    from qf_lib.data_providers.quandl.quandl_data_provider import QuandlDataProvider
    # from qf_lib.publishers.email_publishing.email_publisher import EmailPublisher
    from qf_lib.settings import Settings

    builder = ContainerBuilder()

    # # PUBLISHERS
    # builder.register_class(EmailPublisher, component_scope=SingleInstance)
    #
    # # DATA PROVIDERS
    # builder.register_class(ReadOnlyDBConnectionProvider, component_scope=SingleInstance)
    # builder.register_class(ReadWriteDBConnectionProvider, component_scope=SingleInstance)
    #
    builder.register_class(QuandlDataProvider, component_scope=SingleInstance)
    # builder.register_class(HaverDataProvider, component_scope=SingleInstance)
    builder.register_class(BloombergDataProvider, component_scope=SingleInstance)
    # builder.register_class(CryptoCurrencyDataProvider, component_scope=SingleInstance)
    # builder.register_class(TimeseriesDataProvider, component_scope=SingleInstance)
    builder.register_class(GeneralPriceProvider, component_scope=SingleInstance)
    #
    # # Data Access Objects for reporting
    # builder.register_class(StStMunichPositionDAO, component_scope=SingleInstance)
    # builder.register_class(DailyReportDAO, component_scope=SingleInstance)
    # builder.register_class(DetailedRiskReportDAO, component_scope=SingleInstance)
    # builder.register_class(TrueViewMonthlyScenariosDAO, component_scope=SingleInstance)
    # builder.register_class(CurrentSensitivitiesDAO, component_scope=SingleInstance)
    #
    # builder.register_class(RiskParityBoxesFactory, component_scope=SingleInstance)
    # builder.register_class(ConvexityPeriodsCalculator, component_scope=SingleInstance)
    #
    # # REPORT GENERATORS
    # # Equity Books Sensitivities Report
    # builder.register_class(SensitivitiesReportFactory, component_scope=SingleInstance)
    # builder.register_class(SensitivitiesSubreportFactory, component_scope=SingleInstance)
    # builder.register_class(SensitivityReportDataDownloader, component_scope=SingleInstance)
    # builder.register_class(SensitivitiesPDFExporter, component_scope=SingleInstance)
    # builder.register_class(SensitivitiesDatabaseExporter, component_scope=SingleInstance)
    #
    # MISCELLANEOUS COMPONENTS
    # builder.register_class(RollingContractsSeriesProducer, component_scope=SingleInstance)
    # builder.register_class(FundHistorySimulator, component_scope=SingleInstance)
    # builder.register_class(RealTimer, component_scope=SingleInstance, register_as=Timer)

    # EXPORTERS / IMPORTERS
    builder.register_class(ExcelExporter, component_scope=SingleInstance)
    builder.register_class(ExcelImporter, component_scope=SingleInstance)
    builder.register_class(PDFExporter, component_scope=SingleInstance)
    builder.register_class(HTMLExporter, component_scope=SingleInstance)

    # OTHER
    settings_dir_path = join(dirname(abspath(__file__)), 'config_files')
    settings_path = join(settings_dir_path, 'demo_settings.json')
    secret_path = join(settings_dir_path, 'demo_secret_settings.json')
    settings = Settings(settings_path, secret_path)
    builder.register_instance(Settings, settings)

    return builder.build()


container = _get_ioc_container()
