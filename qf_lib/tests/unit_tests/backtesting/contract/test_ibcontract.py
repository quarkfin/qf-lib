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
from unittest import TestCase, skipIf

from qf_lib.common.enums.security_type import SecurityType

try:
    from qf_lib.brokers.ib_broker.ib_contract import IBContract
    from ibapi.contract import Contract
    is_ibapi_installed = True
except ImportError:
    is_ibapi_installed = False


@skipIf(not is_ibapi_installed, "No Interactive Brokers API installed. Tests are being skipped.")
class TestIBContract(TestCase):

    def test_futures_ibcontract_from_ib_contract(self):
        contract = Contract()
        contract.symbol = "ES"
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "20190307"
        contract.multiplier = "5"

        ibcontract = IBContract.from_ib_contract(contract)
        self.assertEqual(ibcontract.symbol, "ES")
        self.assertEqual(ibcontract.secType, "FUT")
        self.assertEqual(ibcontract.security_type, SecurityType.FUTURE)
        self.assertEqual(ibcontract.exchange, "GLOBEX")
        self.assertEqual(ibcontract.currency, "USD")
        self.assertEqual(ibcontract.lastTradeDateOrContractMonth, "20190307")
        self.assertEqual(ibcontract.last_trade_date, datetime(2019, 3, 7))
        self.assertEqual(ibcontract.multiplier, "5")

    def test_futures_ibcontract_from_ib_contract_2(self):
        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = "ESU6"

        ibcontract = IBContract.from_ib_contract(contract)

        self.assertEqual(ibcontract.secType, "FUT")
        self.assertEqual(ibcontract.security_type, SecurityType.FUTURE)
        self.assertEqual(ibcontract.exchange, "GLOBEX")
        self.assertEqual(ibcontract.currency, "USD")
        self.assertEqual(ibcontract.localSymbol, "ESU6")

    def test_stock_ibcontract_from_ib_contract(self):
        contract = Contract()
        contract.symbol = "MSFT"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        contract.primaryExchange = "ISLAND"

        ibcontract = IBContract.from_ib_contract(contract)

        self.assertEqual(ibcontract.symbol, "MSFT")
        self.assertEqual(ibcontract.secType, "STK")
        self.assertEqual(ibcontract.security_type, SecurityType.STOCK)
        self.assertEqual(ibcontract.exchange, "SMART")
        self.assertEqual(ibcontract.currency, "USD")
        self.assertEqual(ibcontract.primaryExchange, "ISLAND")

    def test_index_ibcontract_from_ib_contract(self):
        contract = Contract()
        contract.symbol = "DAX"
        contract.secType = "IND"
        contract.currency = "EUR"
        contract.exchange = "DTB"

        ibcontract = IBContract.from_ib_contract(contract)

        self.assertEqual(ibcontract.symbol, "DAX")
        self.assertEqual(ibcontract.secType, "IND")
        self.assertEqual(ibcontract.security_type, SecurityType.INDEX)
        self.assertEqual(ibcontract.exchange, "DTB")
        self.assertEqual(ibcontract.currency, "EUR")

    def test_futures_ibcontract_from_string(self):
        contract_string = "0,ES,FUT,20190307,0.0,,5,GLOBEX,,USD,,,False,,combo:"
        ibcontract = IBContract.from_string(contract_string)

        self.assertEqual(ibcontract.symbol, "ES")
        self.assertEqual(ibcontract.secType, "FUT")
        self.assertEqual(ibcontract.security_type, SecurityType.FUTURE)
        self.assertEqual(ibcontract.exchange, "GLOBEX")
        self.assertEqual(ibcontract.currency, "USD")
        self.assertEqual(ibcontract.lastTradeDateOrContractMonth, "20190307")
        self.assertEqual(ibcontract.last_trade_date, datetime(2019, 3, 7))
        self.assertEqual(ibcontract.multiplier, "5")

    def test_futures_ibcontract_from_string_2(self):
        contract_string = "0,,FUT,,0.0,,,GLOBEX,,USD,ESU6,,False,,combo:"
        ibcontract = IBContract.from_string(contract_string)
        self.assertEqual(ibcontract.secType, "FUT")
        self.assertEqual(ibcontract.security_type, SecurityType.FUTURE)
        self.assertEqual(ibcontract.exchange, "GLOBEX")
        self.assertEqual(ibcontract.currency, "USD")
        self.assertEqual(ibcontract.localSymbol, "ESU6")

    def test_stock_ibcontract_from_string(self):
        contract_string = "0,MSFT,STK,,0.0,,,SMART,ISLAND,USD,,,False,,combo:"
        ibcontract = IBContract.from_string(contract_string)

        self.assertEqual(ibcontract.symbol, "MSFT")
        self.assertEqual(ibcontract.secType, "STK")
        self.assertEqual(ibcontract.security_type, SecurityType.STOCK)
        self.assertEqual(ibcontract.exchange, "SMART")
        self.assertEqual(ibcontract.currency, "USD")
        self.assertEqual(ibcontract.primaryExchange, "ISLAND")

    def test_index_ibcontract_from_string(self):
        contract_string = "0,DAX,IND,,0.0,,,DTB,,EUR,,,False,,combo:"
        ibcontract = IBContract.from_string(contract_string)

        self.assertEqual(ibcontract.symbol, "DAX")
        self.assertEqual(ibcontract.secType, "IND")
        self.assertEqual(ibcontract.security_type, SecurityType.INDEX)
        self.assertEqual(ibcontract.exchange, "DTB")
        self.assertEqual(ibcontract.currency, "EUR")

    def test_futures_spread_ibcontract_from_string(self):
        string = "0,VIX,BAG,,0.0,,,CFE,,USD,,,False,,combo:;326501438,1,BUY,CFE,0,0,,-1;323072528,1,SELL,CFE,0,0,,-1"
        ibcontract = IBContract.from_string(string)

        self.assertEqual(ibcontract.symbol, "VIX")
        self.assertEqual(ibcontract.security_type, SecurityType.SPREAD)
        self.assertEqual(ibcontract.secType, "BAG")
        self.assertEqual(ibcontract.currency, "USD")
        self.assertEqual(ibcontract.exchange, "CFE")
        self.assertEqual(len(ibcontract.comboLegs), 2)

        self.assertEqual(ibcontract.comboLegs[0].conId, 326501438)
        self.assertEqual(ibcontract.comboLegs[0].ratio, 1)
        self.assertEqual(ibcontract.comboLegs[0].action, "BUY")
        self.assertEqual(ibcontract.comboLegs[0].exchange, "CFE")

        self.assertEqual(ibcontract.comboLegs[1].conId, 323072528)
        self.assertEqual(ibcontract.comboLegs[1].ratio, 1)
        self.assertEqual(ibcontract.comboLegs[1].action, "SELL")
        self.assertEqual(ibcontract.comboLegs[1].exchange, "CFE")
