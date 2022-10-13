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

from os.path import join, dirname, abspath


def _get_ioc_container():
    """
    Creates and returns the IoC container. If it already exists the existing instance is returned.

    WARNING: Container shall be used explicitly only in the scripts and NOWHERE ELSE!!! You better don't try to violate
    this rule or I'll find you.
    """
    from dic.container import ContainerBuilder
    from dic.scope import SingleInstance

    from qf_lib.backtesting.trading_session.backtest_trading_session_builder import BacktestTradingSessionBuilder
    from qf_lib.common.risk_parity_boxes.risk_parity_boxes import RiskParityBoxesFactory
    from qf_lib.common.utils.dateutils.timer import RealTimer
    from qf_lib.common.utils.dateutils.timer import Timer
    from qf_lib.documents_utils.document_exporting.html_exporter import HTMLExporter
    from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
    from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
    from qf_lib.documents_utils.excel.excel_importer import ExcelImporter
    from qf_lib.documents_utils.email_publishing.email_publisher import EmailPublisher
    from qf_lib.settings import Settings

    builder = ContainerBuilder()

    # PUBLISHERS
    builder.register_class(EmailPublisher, component_scope=SingleInstance)

    # MISCELLANEOUS COMPONENTS
    builder.register_class(BacktestTradingSessionBuilder, component_scope=SingleInstance)
    builder.register_class(RiskParityBoxesFactory, component_scope=SingleInstance)

    # EXPORTERS / IMPORTERS
    builder.register_class(ExcelExporter, component_scope=SingleInstance)
    builder.register_class(ExcelImporter, component_scope=SingleInstance)
    builder.register_class(PDFExporter, component_scope=SingleInstance)
    builder.register_class(HTMLExporter, component_scope=SingleInstance)
    builder.register_class(RealTimer, component_scope=SingleInstance, register_as=Timer)

    # OTHER
    settings_dir_path = join(dirname(abspath(__file__)), 'config_files')
    settings_path = join(settings_dir_path, 'demo_settings.json')
    secret_path = join(settings_dir_path, 'demo_secret_settings.json')
    settings = Settings(settings_path, secret_path)
    builder.register_instance(Settings, settings)

    return builder.build()


container = _get_ioc_container()
