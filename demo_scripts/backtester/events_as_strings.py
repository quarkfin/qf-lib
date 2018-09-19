from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.transaction import Transaction
from qf_lib.common.utils.dateutils.string_to_date import str_to_date

time = str_to_date("2010-01-01")
ticker = Contract("MSFT US Equity", security_type='SEK', exchange='TEST_XCHANGE')
quantity = 13
price = 100.5
commission = 1.2

transaction = Transaction(time, ticker, quantity, price, commission)

print(transaction)
