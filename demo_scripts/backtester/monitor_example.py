import time
from datetime import timedelta
from random import randint

import matplotlib.pyplot as plt

plt.ion()  # required for dynamic chart

# order of the imports is important. BacktestMonitor has to be imported before anything else form qf_lib
from qf_lib.backtesting.monitoring.backtest_monitor import BacktestMonitor
from qf_lib.common.utils.excel.excel_exporter import ExcelExporter
from qf_common.config.ioc import container
from qf_lib.backtesting.backtest_result.backtest_result import BacktestResult
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.transaction import Transaction
from qf_lib.backtesting.portfolio.portfolio import Portfolio
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.document_exporting.pdf_exporter import PDFExporter
from qf_lib.settings import Settings

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
portfolio.dates.append(start_date)
# noinspection PyProtectedMember
portfolio.portfolio_values.append(initial_value)

# create an Transaction
timestamp = str_to_date("2010-01-01")
ticker = BloombergTicker("MSFT US Equity")
contract = Contract("MSFT US Equity", security_type="STK", exchange="NYSE")
quantity = 13
price = 100.5
commission = 1.2
transaction = Transaction(timestamp, contract, quantity, price, commission)

for i in range(50):
    date = start_date + timedelta(days=i)
    # noinspection PyProtectedMember
    past_value = portfolio.portfolio_values[-1]
    rand = randint(0, 100) - 50

    # noinspection PyProtectedMember
    portfolio.dates.append(date)
    # noinspection PyProtectedMember
    portfolio.portfolio_values.append(past_value + rand)

    monitor.end_of_day_update(date)
    monitor.record_transaction(transaction)
    time.sleep(0.1)

monitor.end_of_trading_update()
