"""
Copyright (C) 2016 Interactive Brokers LLC. All rights reserved.  This code is
subject to the terms and conditions of the IB API Non-Commercial License or the
 IB API Commercial License, as applicable.
"""

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
from ibapi.contract import Contract, ComboLeg


class ContractSamples:
    """ Usually, the easiest way to define a Stock/CASH contract is through
    these four attributes.  """

    @staticmethod
    def EurGbpFx():
        contract = Contract()
        contract.symbol = "EUR"
        contract.secType = "CASH"
        contract.currency = "GBP"
        contract.exchange = "IDEALPRO"
        return contract

    @staticmethod
    def Index():
        contract = Contract()
        contract.symbol = "DAX"
        contract.secType = "IND"
        contract.currency = "EUR"
        contract.exchange = "DTB"
        return contract

    @staticmethod
    def CFD():
        contract = Contract()
        contract.symbol = "IBDE30"
        contract.secType = "CFD"
        contract.currency = "EUR"
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def EuropeanStock():
        contract = Contract()
        contract.symbol = "SIE"
        contract.secType = "STK"
        contract.currency = "EUR"
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def OptionAtIse():
        contract = Contract()
        contract.symbol = "BPX"
        contract.secType = "OPT"
        contract.currency = "USD"
        contract.exchange = "ISE"
        contract.lastTradeDateOrContractMonth = "20160916"
        contract.right = "C"
        contract.strike = 65
        contract.multiplier = "100"
        return contract

    @staticmethod
    def BondWithCusip():
        contract = Contract()
        # enter CUSIP as symbol
        contract.symbol = "912828C57"
        contract.secType = "BOND"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    @staticmethod
    def Bond():
        contract = Contract()
        contract.conId = 267433416
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def MutualFund():
        contract = Contract()
        contract.symbol = "VINIX"
        contract.secType = "FUND"
        contract.exchange = "FUNDSERV"
        contract.currency = "USD"
        return contract

    @staticmethod
    def Commodity():
        contract = Contract()
        contract.symbol = "XAUUSD"
        contract.secType = "CMDTY"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    @staticmethod
    def USStock():
        contract = Contract()
        contract.symbol = "IBKR"
        contract.secType = "STK"
        contract.currency = "USD"
        # In the API side, NASDAQ is always defined as ISLAND in the exchange field
        contract.exchange = "ISLAND"
        return contract

    @staticmethod
    def USStockWithPrimaryExch():
        contract = Contract()
        contract.symbol = "MSFT"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        # Specify the Primary Exchange attribute to avoid contract ambiguity
        # (there is an ambiguity because there is also a MSFT contract with primary exchange = "AEB")
        contract.primaryExchange = "ISLAND"
        return contract

    @staticmethod
    def USStockAtSmart():
        contract = Contract()
        contract.symbol = "IBKR"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"
        return contract

    @staticmethod
    def USOptionContract():
        contract = Contract()
        contract.symbol = "GOOG"
        contract.secType = "OPT"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "20170120"
        contract.strike = 615
        contract.right = "C"
        contract.multiplier = "100"
        return contract

    @staticmethod
    def OptionAtBOX():
        contract = Contract()
        contract.symbol = "GOOG"
        contract.secType = "OPT"
        contract.exchange = "BOX"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "20170120"
        contract.strike = 615
        contract.right = "C"
        contract.multiplier = "100"
        return contract

    """ Option contracts require far more information since there are many
    contracts having the exact same attributes such as symbol, currency,
    strike, etc. This can be overcome by adding more details such as the
    trading class"""

    @staticmethod
    def OptionWithTradingClass():
        # ! [optcontract_tradingclass]
        contract = Contract()
        contract.symbol = "SANT"
        contract.secType = "OPT"
        contract.exchange = "MEFFRV"
        contract.currency = "EUR"
        contract.lastTradeDateOrContractMonth = "20190621"
        contract.strike = 7.5
        contract.right = "C"
        contract.multiplier = "100"
        contract.tradingClass = "SANEU"
        # ! [optcontract_tradingclass]
        return contract

    """ Using the contract's own symbol (localSymbol) can greatly simplify a
    contract description """

    @staticmethod
    def OptionWithLocalSymbol():
        contract = Contract()
        # Watch out for the spaces within the local symbol!
        contract.localSymbol = "C DBK  DEC 20  1600"
        contract.secType = "OPT"
        contract.exchange = "DTB"
        contract.currency = "EUR"
        return contract

    """ Dutch Warrants (IOPTs) can be defined using the local symbol or conid
    """

    @staticmethod
    def DutchWarrant():
        contract = Contract()
        contract.localSymbol = "B881G"
        contract.secType = "IOPT"
        contract.exchange = "SBF"
        contract.currency = "EUR"
        return contract

    """ Future contracts also require an expiration date but are less
    complicated than options."""

    @staticmethod
    def SimpleFuture():
        contract = Contract()
        contract.symbol = "ES"
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "201612"
        return contract

    """Rather than giving expiration dates we can also provide the local symbol
    attributes such as symbol, currency, strike, etc. """

    @staticmethod
    def FutureWithLocalSymbol():
        contract = Contract()
        contract.secType = "FUT"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.localSymbol = "ESU6"
        return contract

    @staticmethod
    def FutureWithMultiplier():
        contract = Contract()
        contract.symbol = "DAX"
        contract.secType = "FUT"
        contract.exchange = "DTB"
        contract.currency = "EUR"
        contract.lastTradeDateOrContractMonth = "201609"
        contract.multiplier = "5"
        return contract

    """ Note the space in the symbol! """

    @staticmethod
    def WrongContract():
        contract = Contract()
        contract.symbol = " IJR "
        contract.conId = 9579976
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    @staticmethod
    def FuturesOnOptions():
        contract = Contract()
        contract.symbol = "SPX"
        contract.secType = "FOP"
        contract.exchange = "GLOBEX"
        contract.currency = "USD"
        contract.lastTradeDateOrContractMonth = "20180315"
        contract.strike = 1025
        contract.right = "C"
        contract.multiplier = "250"
        return contract

    """ It is also possible to define contracts based on their ISIN (IBKR STK
    sample). """

    @staticmethod
    def ByISIN():
        contract = Contract()
        contract.secIdType = "ISIN"
        contract.secId = "US45841N1072"
        contract.exchange = "SMART"
        contract.currency = "USD"
        contract.secType = "STK"
        return contract

    """ Or their conId (EUR.uSD sample).
    Note: passing a contract containing the conId can cause problems if one of
    the other provided attributes does not match 100% with what is in IB's
    database. This is particularly important for contracts such as Bonds which
    may change their description from one day to another.
    If the conId is provided, it is best not to give too much information as
    in the example below. """

    @staticmethod
    def ByConId():
        contract = Contract()
        contract.secType = "CASH"
        contract.conId = 12087792
        contract.exchange = "IDEALPRO"
        return contract

    """ Ambiguous contracts are great to use with reqContractDetails. This way
    you can query the whole option chain for an underlying. Bear in mind that
    there are pacing mechanisms in place which will delay any further responses
    from the TWS to prevent abuse. """

    @staticmethod
    def OptionForQuery():
        contract = Contract()
        contract.symbol = "FISV"
        contract.secType = "OPT"
        contract.exchange = "SMART"
        contract.currency = "USD"
        return contract

    @staticmethod
    def OptionComboContract():
        contract = Contract()
        contract.symbol = "DBK"
        contract.secType = "BAG"
        contract.currency = "EUR"
        contract.exchange = "DTB"

        leg1 = ComboLeg()
        leg1.conId = 197397509  # DBK JUN 15 2018 C
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "DTB"

        leg2 = ComboLeg()
        leg2.conId = 197397584  # DBK JUN 15 2018 P
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "DTB"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        return contract

    """ STK Combo contract
    Leg 1: 43645865 - IBKR's STK
    Leg 2: 9408 - McDonald's STK """

    @staticmethod
    def StockComboContract():
        contract = Contract()
        contract.symbol = "IBKR,MCD"
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "SMART"

        leg1 = ComboLeg()
        leg1.conId = 43645865  # IBKR STK
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "SMART"

        leg2 = ComboLeg()
        leg2.conId = 9408  # MCD STK
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "SMART"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        return contract

    """ CBOE Volatility Index Future combo contract """

    @staticmethod
    def FutureComboContract():
        contract = Contract()
        contract.symbol = "VIX"
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "CFE"

        leg1 = ComboLeg()
        leg1.conId = 256038899  # VIX FUT 201708
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "CFE"

        leg2 = ComboLeg()
        leg2.conId = 260564703  # VIX FUT 201709
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "CFE"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        return contract

    @staticmethod
    def SmartFutureComboContract():
        contract = Contract()
        contract.symbol = "WTI"  # WTI,COIL spread. Symbol can be defined as first leg symbol ("WTI") or currency ("USD")
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "SMART"

        leg1 = ComboLeg()
        leg1.conId = 55928698  # WTI future June 2017
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "IPE"

        leg2 = ComboLeg()
        leg2.conId = 55850663  # COIL future June 2017
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "IPE"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        return contract

    @staticmethod
    def InterCmdtyFuturesContract():
        contract = Contract()
        contract.symbol = "CL.BZ"  # symbol is 'local symbol' of intercommodity spread.
        contract.secType = "BAG"
        contract.currency = "USD"
        contract.exchange = "NYMEX"

        leg1 = ComboLeg()
        leg1.conId = 47207310  # CL Dec'16 @NYMEX
        leg1.ratio = 1
        leg1.action = "BUY"
        leg1.exchange = "NYMEX"

        leg2 = ComboLeg()
        leg2.conId = 47195961  # BZ Dec'16 @NYMEX
        leg2.ratio = 1
        leg2.action = "SELL"
        leg2.exchange = "NYMEX"

        contract.comboLegs = []
        contract.comboLegs.append(leg1)
        contract.comboLegs.append(leg2)
        return contract

    @staticmethod
    def NewsFeedForQuery():
        # ! [newsfeedforquery]
        contract = Contract()
        contract.secType = "NEWS"
        contract.exchange = "BT"  # Briefing Trader
        # ! [newsfeedforquery]
        return contract

    @staticmethod
    def BTbroadtapeNewsFeed():
        contract = Contract()
        contract.symbol = "BT:BT_ALL"  # BroadTape All News
        contract.secType = "NEWS"
        contract.exchange = "BT"  # Briefing Trader
        return contract

    @staticmethod
    def BZbroadtapeNewsFeed():
        contract = Contract()
        contract.symbol = "BZ:BZ_ALL"  # BroadTape All News
        contract.secType = "NEWS"
        contract.exchange = "BZ"  # Benzinga Pro
        return contract

    @staticmethod
    def FLYbroadtapeNewsFeed():
        contract = Contract()
        contract.symbol = "FLY:FLY_ALL"  # BroadTape All News
        contract.secType = "NEWS"
        contract.exchange = "FLY"  # Fly on the Wall
        return contract

    @staticmethod
    def MTbroadtapeNewsFeed():
        contract = Contract()
        contract.symbol = "MT:MT_ALL"  # BroadTape All News
        contract.secType = "NEWS"
        contract.exchange = "MT"  # Midnight Trader
        return contract

    @staticmethod
    def ContFut():
        contract = Contract()
        contract.symbol = "ES"
        contract.secType = "CONTFUT"
        contract.exchange = "GLOBEX"
        return contract

    @staticmethod
    def ContAndExpiringFut():
        contract = Contract()
        contract.symbol = "ES"
        contract.secType = "FUT+CONTFUT"
        contract.exchange = "GLOBEX"
        return contract

    @staticmethod
    def JefferiesContract():
        contract = Contract()
        contract.symbol = "AAPL"
        contract.secType = "STK"
        contract.exchange = "JEFFALGO"
        contract.currency = "USD"
        return contract

    @staticmethod
    def CSFBContract():
        contract = Contract()
        contract.symbol = "IBKR"
        contract.secType = "STK"
        contract.exchange = "CSFBALGO"
        contract.currency = "USD"
        return contract
