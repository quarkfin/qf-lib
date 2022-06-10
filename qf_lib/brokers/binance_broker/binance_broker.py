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
import math
import traceback
from datetime import datetime
from typing import Sequence, Optional, List, Dict

import numpy as np
from binance import Client
from binance.enums import SIDE_BUY, ORDER_TYPE_MARKET, SIDE_SELL
from binance.exceptions import BinanceAPIException

from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.order.execution_style import MarketOrder, ExecutionStyle
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.backtesting.portfolio.transaction import Transaction
from qf_lib.brokers.binance_broker.binance_contract_ticker_mapper import BinanceContractTickerMapper
from qf_lib.brokers.binance_broker.binance_position import BinancePosition
from qf_lib.common.blotter.blotter import Blotter
from qf_lib.common.utils.logging.qf_parent_logger import qf_logger
from qf_lib.common.utils.miscellaneous.constants import ISCLOSE_REL_TOL, ISCLOSE_ABS_TOL
from qf_lib.settings import Settings


class BinanceBroker(Broker):
    """
    Synchronous Binance Broker implementing all basic functions of the Broker interface

    Parameters
    -----------
    contract_ticker_mapper: BinanceContractTickerMapper
        specific for Binance contract ticker mapper. The mapper provides the functionality which allows to map a ticker
        with proper quote currency. Please note that all tickers from orders should have the same quote ccy as
        the contract ticker mapper
    blotter: Blotter
        instance of a blotter class to save all transactions.
        Most common implementation of blotters are with use of a CSV file, XLSX file or a database
    settings: Settings
        settings containing all necessary information (in particular API and API secret keys)
    """

    def __init__(self, contract_ticker_mapper: BinanceContractTickerMapper, blotter: Blotter, settings: Settings):
        super().__init__(contract_ticker_mapper)

        self.settings = settings

        self.stable_coins = ['USDT', 'BUSD']
        self.time_in_force_to_string = {TimeInForce.GTC: 'GTC'}

        api_key = settings.binance_api
        api_secret = settings.binance_secret
        self.client = Client(api_key, api_secret)

        self.logger = qf_logger.getChild(self.__class__.__name__)
        self.logger.info(f"Created successfully {self.__class__.__name__}")
        self.blotter = blotter

    def get_positions(self) -> List[Position]:
        self.logger.info("Calling get_positions")

        res = self.client.get_account()
        balances = res['balances']

        positions = []
        for balance in balances:
            ticker = self.contract_ticker_mapper.contract_to_ticker(balance['asset'])
            position_value = float(balance['free'])
            positions.append(BinancePosition(ticker, position_value))

        positions = [position for position in positions if not math.isclose(position.quantity(), 0,
                                                                            rel_tol=ISCLOSE_REL_TOL,
                                                                            abs_tol=ISCLOSE_ABS_TOL)]

        self.logger.info('Positions:')
        for position in positions:
            self.logger.info(position)

        return positions

    def get_open_orders(self) -> Optional[List[Order]]:
        self.logger.info("Calling get_open_orders")

        str_to_time_in_force = {value: key for key, value in self.time_in_force_to_string.items()}
        open_orders = self.client.get_open_orders()

        all_orders = []
        for open_order in open_orders:
            ticker = self.contract_ticker_mapper.contract_to_ticker(open_order['symbol'])
            quantity = float(open_order['origQty'])
            execution_style = MarketOrder()
            time_in_force = str_to_time_in_force.get(open_order['timeInForce'])
            current_order = Order(ticker=ticker, quantity=quantity, execution_style=execution_style,
                                  time_in_force=time_in_force)
            all_orders.append(current_order)

        self.logger.info("Opened orders:")
        for order in all_orders:
            self.logger.info(order)

        return all_orders

    def cancel_order(self, order_id: int, symbol: str):
        self.logger.info(f'Cancelling order. Order ID: {order_id} for symbol {symbol}')
        response = self.client.cancel_order(order_id=order_id, symbol=symbol)
        self.logger.info(f"Response for order {order_id}: {response}")

    def cancel_all_open_orders(self):
        open_orders = self.client.get_open_orders()
        for response in open_orders:
            symbol = response['symbol']
            order_id = response['orderId']
            self.cancel_order(order_id=order_id, symbol=symbol)

    def place_orders(self, orders: Sequence[Order]) -> List[Transaction]:
        if not orders:
            self.logger.info("Empty order list. place_orders quits")
            return []

        tickers = [order.ticker for order in orders]
        if not all([ticker.quote_ccy == self.contract_ticker_mapper.quote_ccy for ticker in tickers]):
            raise ValueError(f'Not all tickers are expressed in the same quote currency. '
                             f'Expected quote currency:  {self.contract_ticker_mapper.quote_ccy}')

        transaction_list = []
        self.logger.info("Placing orders:")
        for order in orders:
            self.logger.info(order)
            transaction = self._place_order(order)
            transaction_list.append(transaction)

        return transaction_list

    def _place_order(self, order: Order) -> Transaction:
        try:
            assert not math.isclose(order.quantity, 0, rel_tol=ISCLOSE_REL_TOL, abs_tol=ISCLOSE_ABS_TOL)
            symbol = self.contract_ticker_mapper.ticker_to_contract(order.ticker)
            side = SIDE_BUY if order.quantity > 0 else SIDE_SELL
            exec_style_type = self._get_execution_style(order.execution_style)
            quantity = abs(order.quantity)
            self.logger.info(f'Sending order with params: Symbol: {symbol}, side: {side}, '
                             f'type: {exec_style_type}, quantity: {quantity}')

            response = self.client.create_order(
                symbol=symbol,
                side=side,
                type=exec_style_type,
                quantity=quantity)

            self.logger.info(f"Response: {response}")
            transaction = self._create_transaction(response, order)
            self.blotter.save_transaction(transaction)
            self.logger.info(f"Transaction recorded: {transaction}")
            return transaction
        except BinanceAPIException as ex:
            self.logger.info(f'Order rejected by exchange: {ex}')
            self.logger.error(traceback.format_exc())
        except Exception as ex:
            self.logger.info(f'Placing order: failed: {ex}')
            self.logger.error(traceback.format_exc())

    def get_portfolio_value(self) -> float:
        self.logger.info("Calling get_portfolio_value")

        portfolio_value = 0
        positions = self.get_positions()
        for counter, position in enumerate(positions):
            self.logger.info(f"{counter}/{len(positions)} {position}")
            symbol = self.contract_ticker_mapper.ticker_to_contract(position.ticker())
            try:
                if symbol in self.stable_coins:
                    price_in_usd = 1
                else:
                    price_in_usd = float(self.client.get_symbol_ticker(symbol=symbol)['price'])
            except Exception as ex:
                self.logger.error(f'{ex} for symbol {symbol}')
                self.logger.error(traceback.format_exc())
                price_in_usd = 0

            value = position.quantity() * price_in_usd
            self.logger.info(f'Value for {symbol}: {value}')
            portfolio_value += value

        self.logger.info(f'Total portfolio value: {portfolio_value} [{self.contract_ticker_mapper.quote_ccy}]')
        return portfolio_value

    def get_exchange_info(self):
        self.logger.info('Calling get_exchange_info')
        return self.client.get_exchange_info()

    def _get_execution_style(self, execution_style: ExecutionStyle):
        if isinstance(execution_style, MarketOrder):
            return ORDER_TYPE_MARKET

        raise NotImplementedError(f'Execution style {execution_style} currently not supported')

    def _create_transaction(self, response: Dict, order: Order) -> Optional[Transaction]:
        try:
            def get_fill_price(fills):
                prices = []
                quantities = []
                for fill in fills:
                    prices.append(float(fill['price']))
                    quantities.append(float(fill['qty']))
                return np.average(prices, weights=quantities)

            def get_total_commission(fills):
                commissions = []
                for fill in fills:
                    comm_asset = fill['commissionAsset']
                    if comm_asset == order.ticker.quote_ccy:
                        multiplier = 1
                    elif comm_asset == order.ticker.currency:
                        multiplier = float(fill['price'])
                    else:
                        self.logger.error(f'Incorrect commissionAsset for fill : {fill}, commission will be 0')
                        multiplier = 0
                    commissions.append(float(fill['commission']) * multiplier)
                return sum(commissions)

            transaction_fill_time = datetime.fromtimestamp(response['transactTime'] / 1000)
            ticker_result = order.ticker
            ticker_result.set_name(response['symbol'])
            quantity = float(response['executedQty'])
            quantity = -quantity if response['side'] == SIDE_SELL else quantity
            price = get_fill_price(response['fills'])
            commission = get_total_commission(response['fills'])
            trade_id = response['orderId']
            account = ""
            strategy = order.strategy
            broker = "Binance"
            currency = self.contract_ticker_mapper.quote_ccy

            t = Transaction(transaction_fill_time, ticker_result, quantity, price, commission, trade_id, account,
                            strategy, broker, currency)
            return t
        except Exception as ex:
            self.logger.error(f'Exception {ex} in parsing response {response}, for order: {order}')
            self.logger.error(traceback.format_exc())
