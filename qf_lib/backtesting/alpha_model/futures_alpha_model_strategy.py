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
from typing import Sequence, List, Set

import numpy as np

from qf_lib.backtesting.alpha_model.alpha_model_strategy import AlphaModelStrategy
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.portfolio.position import Position
from qf_lib.containers.futures.future_ticker import FutureTicker


class FuturesAlphaModelStrategy(AlphaModelStrategy):
    def _place_orders(self, signals):
        self.logger.info("Closing positions with old futures contracts")

        self.logger.info("Converting Signals to Orders using: {}".format(self._position_sizer.__class__.__name__))
        orders = self._position_sizer.size_signals(signals)

        self.logger.info("Close all positions for expired contracts")
        close_orders = self._close_old_futures_contracts(signals)

        self.logger.info("Placing close orders for expired contracts")
        self._broker.place_orders(close_orders)

        self.logger.info("Cancelling all open orders")
        self._broker.cancel_all_open_orders()

        market_orders = [order for order in orders if isinstance(order.execution_style, MarketOrder)]
        self.logger.info("Placing market orders")
        self._broker.place_orders(market_orders)

        if self._use_stop_losses:
            stop_orders = [order for order in orders if isinstance(order.execution_style, StopOrder)]
            self.logger.info("Placing stop orders")
            self._broker.place_orders(stop_orders)

    def _close_old_futures_contracts(self, signals: Sequence[Signal]) -> Sequence[Order]:
        # Close contracts for which a new futures contract from the same futures family should be open
        open_positions = self._broker.get_positions()
        # Get all futures contracts, for which there exist an open position in the portfolio
        open_positions_contracts = [position.contract() for position in open_positions
                                    if position.contract().security_type == 'FUT']

        # Get all futures tickers from the list of signals
        signals_future_tickers = [signal.ticker for signal in signals if isinstance(signal.ticker, FutureTicker)]
        # Get the list of strings, representing specific tickers, from signals list
        signals_future_tickers_strings = {ticker.ticker for ticker in signals_future_tickers}  # type: Set[str]

        def belongs_to_any_of_future_families(contract: Contract, future_tickers_list: List[FutureTicker]):
            # Check if the given Contract corresponds to a ticker, which belong to the same futures contracts family
            # as any of the FutureTickers from the given list
            ticker = self._contract_ticker_mapper.contract_to_ticker(contract, strictly_to_specific_ticker=False)
            for future_ticker in future_tickers_list:
                if future_ticker.belongs_to_family(ticker):
                    return True
            return False

        # Get these contracts, for which a signal has been generated, while in the same time
        # there exists an open position with another futures contract from the same futures family
        expired_contracts = {
            contract for contract in open_positions_contracts
            if belongs_to_any_of_future_families(contract, signals_future_tickers) and
               contract.symbol not in signals_future_tickers_strings
        }

        # Create close market orders for each of the overlapping, old future contracts
        market_order_list = self._order_factory.target_percent_orders(
            {contract: 0 for contract in expired_contracts}, MarketOrder(), TimeInForce.GTC
        )

        return market_order_list

    def _get_current_exposure(self, contract: Contract, current_positions: List[Position]) -> Exposure:

        def matching_contract(contract1: Contract, contract2: Contract, strictly_to_specific_ticker) -> bool:
            # Check if the two given contracts are the same (in case of contracts of STK security type) or if they
            # belong to the same futures contracts family (in case of futures contracts)
            if contract1.security_type == 'STK' and contract2.security_type == 'STK':
                return contract1 == contract2
            elif contract1.security_type == 'FUT' and contract2.security_type == 'FUT':
                future_contract1 = self._contract_ticker_mapper.contract_to_ticker(contract1,
                                                                                   strictly_to_specific_ticker=strictly_to_specific_ticker)
                # type: FutureTicker
                future_contract2 = self._contract_ticker_mapper.contract_to_ticker(contract2,
                                                                                   strictly_to_specific_ticker=strictly_to_specific_ticker)
                # type: FutureTicker
                if not strictly_to_specific_ticker:
                    return future_contract1.belongs_to_family(future_contract2)
                else:
                    return future_contract1 == future_contract2
            else:
                return False

        matching_position_quantities = [position.quantity() for position in current_positions if
                                        matching_contract(position.contract(), contract, False)]

        assert len(matching_position_quantities) in [0, 1, 2]

        if len(matching_position_quantities) is 2:
            # The position for the previous contract is still open (it was not possible to close the position - e.g.
            # no prices for this contract) and the position for the new contract has been already opened
            # In this case, we need to match the position based on the specific ticker
            print("Matching positions: {}".format(len(matching_position_quantities)))
            matching_position_quantities = [position.quantity() for position in current_positions if
                                            matching_contract(position.contract(), contract, True)]

        quantity = next(iter(matching_position_quantities), 0)
        current_exposure = Exposure(np.sign(quantity))
        return current_exposure

    def _save_signals(self, signals: List[Signal]):
        tickers_to_models = {
            ticker: model.__class__.__name__ for model, tickers_list in self._model_tickers_dict.items()
            for ticker in tickers_list
        }

        tickers_to_signals = {
            ticker: None for model_tickers in self._model_tickers_dict.values() for ticker in model_tickers
        }

        tickers_to_signals.update({
            signal.ticker: signal for signal in signals
        })

        for ticker in tickers_to_signals.keys():
            signal = tickers_to_signals[ticker]
            model_name = tickers_to_models[ticker]

            self.logger.info(signal)
            if isinstance(ticker, FutureTicker):
                ticker_str = ticker.family_id + "@" + model_name
            else:
                ticker_str = ticker.as_string() + "@" + model_name
            self._signals[ticker_str].append((self._timer.now().date(), signal))

        self._signals_dates.append(self._timer.now())
