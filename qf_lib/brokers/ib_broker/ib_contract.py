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
from typing import Optional

from ibapi.contract import Contract, DeltaNeutralContract, ComboLeg
from ibapi.utils import iswrapper

from qf_lib.common.enums.security_type import SecurityType


class IBContract(Contract):
    """ Wrapper around the Interactive Brokers Contract object, which facilitates the usage and integration of contracts
    into the qf-lib workflow. IBContract object can be generated directly from Tickers using the IBContractTickerMapper
    and then sent to the Broker inside orders.

    Parameters
    ----------
    symbol: str
        symbol of the asset, as defined by the Interactive Brokers
    security_type: SecurityType
        type of the security, which is later on mapped on the corresponding IB security type code
    multiplier: str
        size of the contract, as defined by the Interactive Brokers (should be a string value)
    currency: str
        currency of the contract (e.g. USD, EUR)
    last_trade_date: Optional[datetime]
        optional parameter pointing to the last trade date of the contract (applicable to e.g. futures contracts)
    """

    security_type_map = {
        SecurityType.FUTURE: "FUT",
        SecurityType.STOCK: "STK",
        SecurityType.INDEX: "IND",
        SecurityType.SPREAD: "BAG",
        SecurityType.CONFUT: "CONFUT"
    }

    @iswrapper
    def __init__(self, symbol: str, security_type: SecurityType, exchange: str, multiplier: Optional[str] = "",
                 currency: str = "", last_trade_date: Optional[datetime] = None):
        super().__init__()

        self.symbol = symbol
        self.security_type = security_type
        self.exchange = exchange
        self.currency = currency

        # Valid only for Futures contracts
        self.multiplier = multiplier
        self.last_trade_date = last_trade_date

    @property
    def lastTradeDateOrContractMonth(self) -> str:
        return self.last_trade_date.strftime("%Y%m%d") if self.last_trade_date else ""

    @lastTradeDateOrContractMonth.setter
    def lastTradeDateOrContractMonth(self, lastTradeDateOrContractMonth: str):
        self.last_trade_date = datetime.strptime(lastTradeDateOrContractMonth, "%Y%m%d") if \
            lastTradeDateOrContractMonth != '' else None

    @property
    def secType(self) -> str:
        return self._map_security_type(self.security_type)

    @secType.setter
    def secType(self, secType: str):
        self.security_type = self._map_secType(secType) if secType else None

    @classmethod
    def from_ib_contract(cls, ib_contract: Contract) -> "IBContract":
        """ Create an IBContract from an interactive brokers Contract object. The function returns a new instance
        of an IBContract object. """
        security_type = cls._map_secType(ib_contract.secType)
        ibcontract = IBContract(ib_contract.symbol, security_type, ib_contract.exchange)

        for attribute_name, value in ib_contract.__dict__.items():
            setattr(ibcontract, attribute_name, value)

        return ibcontract

    @classmethod
    def _map_security_type(cls, security_type: SecurityType) -> str:
        try:
            return cls.security_type_map[security_type]
        except KeyError:
            raise ValueError(f"Security type {security_type} could not be mapped into a correct Interactive Brokers "
                             f"secType") from None

    @classmethod
    def _map_secType(cls, secType: str) -> SecurityType:
        security_type_map = {value: key for key, value in cls.security_type_map.items()}
        try:
            return security_type_map[secType]
        except KeyError:
            raise ValueError(f"Security type {secType} could not be mapped into a correct Interactive "
                             f"Brokers secType") from None

    def to_string(self) -> str:
        return str(self)

    @classmethod
    def from_string(cls, contract_str: str) -> "IBContract":
        """ Create IBContract object from the corresponding string. """

        params, combo_legs = contract_str.split("combo:")
        ib_contract = Contract()
        [ib_contract.conId, ib_contract.symbol, ib_contract.secType, ib_contract.lastTradeDateOrContractMonth,
         ib_contract.strike, ib_contract.right, ib_contract.multiplier, ib_contract.exchange,
         ib_contract.primaryExchange, ib_contract.currency, ib_contract.localSymbol, ib_contract.tradingClass,
         ib_contract.includeExpired, ib_contract.secIdType, ib_contract.secId] = params.split(",")

        ib_contract.conId = int(ib_contract.conId)
        ib_contract.strike = float(ib_contract.strike)
        ib_contract.includeExpired = bool(ib_contract.includeExpired == "True")

        combo_legs = combo_legs.split(";")
        combo_legs = [c for c in combo_legs if len(c) > 0]

        if len(combo_legs) > 0:
            if len(combo_legs[-1].split(",")) == 3:
                delta_neutral_contract = combo_legs[-1].split(",")
                combo_legs = combo_legs[:-1]

                ib_contract.deltaNeutralContract = DeltaNeutralContract()
                ib_contract.deltaNeutralContract.conId = int(delta_neutral_contract[0])
                ib_contract.deltaNeutralContract.delta = float(delta_neutral_contract[1])
                ib_contract.deltaNeutralContract.price = float(delta_neutral_contract[2])

            ib_contract.comboLegs = [] if len(combo_legs) > 0 else None
            if ib_contract.comboLegs is not None:
                for params in combo_legs:
                    params = params.split(",")
                    combo_leg = ComboLeg()
                    combo_leg.conId = int(params[0])
                    combo_leg.ratio = int(params[1])
                    combo_leg.action = params[2]
                    combo_leg.exchange = params[3]
                    combo_leg.openClose = int(params[4])
                    combo_leg.shortSaleSlot = int(params[5])
                    combo_leg.designatedLocation = params[6]
                    combo_leg.exemptCode = int(params[7])
                    ib_contract.comboLegs.append(combo_leg)

        return cls.from_ib_contract(ib_contract)

    def __eq__(self, other):
        """ Important: Exchange should not be considered while comparing different IB contracts, as IB always removes
        the exchange information in the contracts that they send inside orders, positions etc. """
        if self is other:
            return True

        if not isinstance(other, IBContract):
            return False

        return (self.symbol, self.secType, self.multiplier, self.last_trade_date) == \
               (other.symbol, other.secType, other.multiplier, other.last_trade_date)

    def __hash__(self):
        return hash((self.symbol, self.secType, self.multiplier))
