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
import unittest
from typing import List
from unittest.mock import patch, call, MagicMock, Mock

from qf_lib.backtesting.alpha_model.alpha_model_strategy import AlphaModelStrategy
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.simulated_bloomberg_mapper import \
    SimulatedBloombergContractTickerMapper
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.containers.futures.future_tickers.bloomberg_future_ticker import BloombergFutureTicker
from qf_lib.containers.futures.futures_rolling_orders_generator import FuturesRollingOrdersGenerator


class TestAlphaModelStrategy(unittest.TestCase):

    def setUp(self) -> None:
        self.ticker = BloombergTicker("Example Ticker")
        self.future_ticker = MagicMock(spec=BloombergFutureTicker)
        self.future_ticker.configure_mock(name="Example", family_id="Example{} Comdty", days_before_exp_date=1,
                                          point_value=1)

        self.alpha_model = MagicMock()

        # Mock trading session
        self.ts = MagicMock()
        self.ts.contract_ticker_mapper = SimulatedBloombergContractTickerMapper()

        self.positions_in_portfolio = []  # type: List[Contract]
        """Contracts for which a position in the portfolio currently exists. This list is used to return backtest
        positions list by the broker."""

        self.ts.broker.get_positions.side_effect = lambda: self.positions_in_portfolio

    def test__get_current_exposure(self):
        """
        Test the result of _get_current_exposure function for a non-future ticker by inspecting the parameters passed to
        alpha models get_signal function.
        """
        expected_current_exposure_values = []
        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.ticker]},
                                                  use_stop_losses=False)
        # In case of empty portfolio get_signal function should have current exposure set to OUT
        alpha_model_strategy.on_before_market_open()
        expected_current_exposure_values.append(Exposure.OUT)

        # Open long position in the portfolio
        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("Example Ticker", "STK", "SIM_EXCHANGE"),
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        expected_current_exposure_values.append(Exposure.LONG)

        # Open short position in the portfolio
        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("Example Ticker", "STK", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        expected_current_exposure_values.append(Exposure.SHORT)

        self.alpha_model.get_signal.assert_has_calls(
            calls=[call(self.ticker, exposure) for exposure in expected_current_exposure_values],
            any_order=False
        )

        # Verify if in case of two positions for the same contract an exception will be raised by the strategy
        self.positions_in_portfolio = [BacktestPositionFactory.create_position(c) for c in (
            Contract("Example Ticker", "STK", "SIM_EXCHANGE"), Contract("Example Ticker", "STK", "SIM_EXCHANGE"))]
        self.assertRaises(AssertionError, alpha_model_strategy.on_before_market_open)

    def test__get_current_exposure__future_ticker(self):
        """
        Test the result of _get_current_exposure function for a future ticker in case of an empty portfolio and in case
        if a position for the given specific ticker exists.
        """
        expected_current_exposure_values = []
        # Set current specific ticker to ExampleZ00 Comdty and open position in the portfolio for the current ticker
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleZ00 Comdty")
        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)
        # In case of empty portfolio get_signal function should have current exposure set to OUT
        futures_alpha_model_strategy.on_before_market_open()
        expected_current_exposure_values.append(Exposure.OUT)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        })]
        futures_alpha_model_strategy.on_before_market_open()
        expected_current_exposure_values.append(Exposure.LONG)

        self.alpha_model.get_signal.assert_has_calls(
            calls=[call(self.future_ticker, exposure) for exposure in expected_current_exposure_values],
            any_order=False
        )

        self.positions_in_portfolio = [BacktestPositionFactory.create_position(c) for c in (
            Contract("ExampleZ00 Comdty", "STK", "SIM_EXCHANGE"), Contract("ExampleZ00 Comdty", "STK", "SIM_EXCHANGE"))]
        self.assertRaises(AssertionError, futures_alpha_model_strategy.on_before_market_open)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__get_current_exposure__future_ticker_rolling(self, generate_close_orders):
        """
        Test the result of _get_current_exposure function for a future ticker in case if a position for an expired
        contract exists in portfolio and the rolling should be performed.
        """
        # Set the future ticker to point to a new specific ticker, different from the one in the position from portfolio
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN01 Comdty")
        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)
        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        })]
        futures_alpha_model_strategy.on_before_market_open()

        self.alpha_model.get_signal.assert_called_once_with(self.future_ticker, Exposure.LONG)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        }), Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        })]
        self.assertRaises(AssertionError, futures_alpha_model_strategy.on_before_market_open)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__get_current_exposure__future_ticker_rolling_2(self, generate_close_orders):
        """
        Test the result of _get_current_exposure function for a future ticker in case if a position for an expired
        contract exists in portfolio and the rolling should be performed.
        """
        # Set the future ticker to point to a new specific ticker, different from the one in the position from portfolio
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN01 Comdty")
        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        }), Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleN01 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        })]
        futures_alpha_model_strategy.on_before_market_open()
        self.alpha_model.get_signal.assert_called_once_with(self.future_ticker, Exposure.LONG)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__get_current_exposure__future_ticker_rolling_3(self, generate_close_orders):
        """
        Test the result of _get_current_exposure function for a future ticker in case if a position for an expired
        contract exists in portfolio and the rolling should be performed.
        """
        # Set the future ticker to point to a new specific ticker, different from the one in the position from portfolio
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN01 Comdty")
        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        }), Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleN01 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        }), Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ01 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        })]
        self.assertRaises(AssertionError, futures_alpha_model_strategy.on_before_market_open)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__adjust_number_of_open_positions_1(self, generate_close_orders):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - there is signal with suggested exposure LONG for Example Ticker
        - Expected output: Example Ticker suggested exposure will be changed to OUT

        In order to test the number of positions adjustment functionality, the get_signal method of alpha model and
        size_signals method od position sizer are mocked and the flow of signals between them is verified.
        """
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN01 Comdty")
        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.ticker]},
                                                  use_stop_losses=False, max_open_positions=1)
        self.alpha_model.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        self.ts.position_sizer.size_signals.assert_called_with(
            [Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1)], False)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__adjust_number_of_open_positions_2(self, generate_close_orders):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - there is a signal with suggested exposure LONG for ExampleN01 Comdty
        - Expected output: ExampleN01 Comdty suggested exposure will be unchanged
        """
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN01 Comdty")
        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                  use_stop_losses=False, max_open_positions=1)
        self.alpha_model.get_signal.return_value = Signal(self.future_ticker, Exposure.LONG, 1)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        self.ts.position_sizer.size_signals.assert_called_with(
            [Signal(self.future_ticker, Exposure.LONG, 1)], False)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__adjust_number_of_open_positions_3(self, generate_close_orders):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - there are 2 LONG signals for ExampleN01 Comdty and Example Ticker
        - Expected output: Example Ticker will be changed to OUT, signal for ExampleN01 Comdty will be unchanged
        """
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN01 Comdty")
        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker, self.ticker]},
                                                  use_stop_losses=False, max_open_positions=1)
        self.alpha_model.get_signal.side_effect = lambda ticker, _: Signal(ticker, Exposure.LONG, 1)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _ = args
        expected_signals = [Signal(self.future_ticker, Exposure.LONG, 1), Signal(self.ticker, Exposure.OUT, 1)]
        self.assertCountEqual(signals, expected_signals)

    def test__adjust_number_of_open_positions_4(self):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - there is signal for ExampleZ00 Comdty with suggested exposure OUT and for Example Ticker - LONG
        - Expected output: Example Ticker will be changed to OUT
        """
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("AN01 Index")

        alpha_model_strategy = AlphaModelStrategy(self.ts,
                                                  {self.alpha_model: [BloombergTicker("ExampleZ00 Comdty"),
                                                                      BloombergTicker("Example Ticker")]},
                                                  use_stop_losses=False, max_open_positions=1)

        exposures = {
            BloombergTicker("ExampleZ00 Comdty"): Exposure.OUT,
            BloombergTicker("Example Ticker"): Exposure.LONG,
        }
        self.alpha_model.get_signal.side_effect = lambda ticker, _: Signal(ticker, exposures[ticker], 1)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _ = args
        expected_signals = [Signal(BloombergTicker("ExampleZ00 Comdty"), Exposure.OUT, 1),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1)]
        self.assertCountEqual(signals, expected_signals)

    def test__adjust_number_of_open_positions__multiple_models(self):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - ExampleZ00 Comdty ane Example Ticker are traded by two independent alpha models
        - there is signal with suggested exposure LONG for Example Ticker and LONG for ExampleZ00 Comdty
        - Expected output: Example Ticker suggested exposure will be changed to OUT
        """
        alpha_model_2 = MagicMock()
        alpha_model_strategy = AlphaModelStrategy(self.ts, {
            self.alpha_model: [BloombergTicker("ExampleZ00 Comdty")],
            alpha_model_2: [BloombergTicker("Example Ticker")]
        }, use_stop_losses=False, max_open_positions=1)

        self.alpha_model.get_signal.return_value = Signal(BloombergTicker("ExampleZ00 Comdty"), Exposure.LONG, 1)
        alpha_model_2.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _ = args
        expected_signals = [Signal(BloombergTicker("ExampleZ00 Comdty"), Exposure.LONG, 1),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1)]
        self.assertCountEqual(signals, expected_signals)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__adjust_number_of_open_positions__multiple_models_2(self, generate_close_orders):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - ExampleZ00 Comdty ane Example Ticker are traded by two independent alpha models
        - there is signal with suggested exposure LONG for Example Ticker and LONG for ExampleN00 Comdty
        - Expected output: Example Ticker suggested exposure will be changed to OUT
        """
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN00 Comdty")
        alpha_model_2 = MagicMock()

        alpha_model_strategy = AlphaModelStrategy(self.ts, {
            self.alpha_model: [self.future_ticker],
            alpha_model_2: [BloombergTicker("Example Ticker")]
        }, use_stop_losses=False, max_open_positions=1)

        self.alpha_model.get_signal.return_value = Signal(self.future_ticker,
                                                          Exposure.LONG, 1)
        alpha_model_2.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _ = args
        expected_signals = [Signal(self.future_ticker, Exposure.LONG, 1),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1)]
        self.assertCountEqual(signals, expected_signals)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__adjust_number_of_open_positions__multiple_models_3(self, generate_close_orders):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - ExampleZ00 Comdty ane Example Ticker are traded by two independent alpha models
        - there is signal with suggested exposure LONG for Example Ticker and OUT for ExampleN00 Comdty
        - Expected output: Example Ticker suggested exposure will be changed to OUT
        """
        self.future_ticker.get_current_specific_ticker.return_value = BloombergTicker("ExampleN00 Comdty")
        alpha_model_2 = MagicMock()

        alpha_model_strategy = AlphaModelStrategy(self.ts, {
            self.alpha_model: [self.future_ticker],
            alpha_model_2: [BloombergTicker("Example Ticker")]
        }, use_stop_losses=False, max_open_positions=1)

        self.alpha_model.get_signal.return_value = Signal(self.future_ticker,
                                                          Exposure.OUT, 1)
        alpha_model_2.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'contract.return_value': Contract("ExampleZ00 Comdty", "FUT", "SIM_EXCHANGE"),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.on_before_market_open()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _ = args
        expected_signals = [Signal(self.future_ticker, Exposure.OUT, 1),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1)]
        self.assertCountEqual(signals, expected_signals)
