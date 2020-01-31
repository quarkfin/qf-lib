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


class Contract(object):
    def __init__(self, symbol: str, security_type: str, exchange: str, contract_size=1):
        """
        Parameters
        ----------
        symbol
            symbol of the asset handled later on by the Broker (e.g. "MSFT")
        security_type
            e.g. 'STK' for a stock
        exchange
            exchange on which the asset should be traded
        """
        self.symbol = symbol
        self.security_type = security_type
        self.exchange = exchange

        # used for futures and options. For cash contracts (stocks, bonds ETFs) should always be equal to 1
        self.contract_size = contract_size

    def __str__(self):
        return 'Contract: symbol: {}, security_type: {} exchange: {}'.format(
            self.symbol, self.security_type, self.exchange)

    def __eq__(self, other):
        if self is other:
            return True

        if not isinstance(other, Contract):
            return False

        return (self.symbol, self.security_type, self.exchange) == (other.symbol, other.security_type, other.exchange)

    def __hash__(self):
        return hash((self.symbol, self.security_type, self.exchange))
