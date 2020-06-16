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
import matplotlib.pyplot as plt
plt.ion()  # required for dynamic chart

from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
# order of the imports is important. BacktestMonitor has to be imported before anything else form qf_lib

from qf_lib.settings import Settings
from qf_lib.documents_utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.monitoring.backtest_result import BacktestResult
from qf_lib.documents_utils.excel.excel_exporter import ExcelExporter
import time
from datetime import timedelta
from random import randint


from demo_scripts.demo_configuration.demo_ioc import container


def main():
    start_date = str_to_date('2018-01-01')
    initial_value = 1000

    portfolio = Portfolio(None, initial_value, None, None)
    backtest_result = BacktestResult(portfolio, 'Monitor Test', start_date=start_date)
    backtest_result.start_time = start_date

    settings = container.resolve(Settings)  # type: Settings
    pdf_exporter = container.resolve(PDFExporter)  # type: PDFExporter
    xlsx_exporter = container.resolve(ExcelExporter)  # type: ExcelExporter
    monitor = BacktestMonitor(backtest_result, settings, pdf_exporter, xlsx_exporter)

    # put first point
    # noinspection PyProtectedMember
    portfolio._dates.append(start_date)
    # noinspection PyProtectedMember
    portfolio._portfolio_values.append(initial_value)

    # create an Transaction
    timestamp = str_to_date("2010-01-01")
    contract = Contract("MSFT US Equity", security_type="STK", exchange="NYSE")
    quantity = 13
    price = 100.5
    commission = 1.2
    transaction = Transaction(timestamp, contract, quantity, price, commission)

    for i in range(50):
        date = start_date + timedelta(days=i)
        # noinspection PyProtectedMember
        past_value = portfolio._portfolio_values[-1]
        rand = randint(0, 100) - 50

        # noinspection PyProtectedMember
        portfolio._dates.append(date)
        # noinspection PyProtectedMember
        portfolio._portfolio_values.append(past_value + rand)

        monitor.end_of_day_update(date)
        monitor.record_transaction(transaction)
        time.sleep(0.1)

    monitor.end_of_trading_update()


if __name__ == '__main__':
    main()
