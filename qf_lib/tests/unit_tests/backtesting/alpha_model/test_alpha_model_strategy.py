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
from unittest.mock import patch, MagicMock, Mock

from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.strategies.alpha_model_strategy import AlphaModelStrategy
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.signals.signal import Signal
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.backtesting.portfolio.position_factory import BacktestPositionFactory
from qf_lib.common.enums.frequency import Frequency
from qf_lib.common.enums.security_type import SecurityType
from qf_lib.common.tickers.tickers import BloombergTicker
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer
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
        self.ts.timer = SettableTimer(str_to_date("2000-01-04 08:00:00.0", DateFormat.FULL_ISO))
        self.ts.frequency = Frequency.DAILY

        self.positions_in_portfolio = []  # type: List[BacktestPosition]
        """Contracts for which a position in the portfolio currently exists. This list is used to return backtest
        positions list by the broker."""

        self.ts.broker.get_positions.side_effect = lambda: self.positions_in_portfolio

    def test__get_current_exposure(self):
        """
        Test the result of _get_current_exposure function for a non-future ticker by inspecting the parameters passed to
        alpha models get_signal function.
        """

        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.ticker]},
                                                  use_stop_losses=False)
        # In case of empty portfolio get_signal function should have current exposure set to OUT
        alpha_model_strategy.calculate_and_place_orders()
        self.alpha_model.get_signal.assert_called_with(self.ticker, Exposure.OUT, self.ts.timer.now(), Frequency.DAILY)

        # Open long position in the portfolio
        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("Example Ticker", SecurityType.STOCK, 1),
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.alpha_model.get_signal.assert_called_with(self.ticker, Exposure.LONG, self.ts.timer.now(), Frequency.DAILY)

        # Open short position in the portfolio
        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("Example Ticker", SecurityType.STOCK, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.alpha_model.get_signal.assert_called_with(self.ticker, Exposure.SHORT, self.ts.timer.now(), Frequency.DAILY)

        # Verify if in case of two positions for the same ticker an exception will be raised by the strategy
        self.positions_in_portfolio = [BacktestPositionFactory.create_position(c) for c in (
            BloombergTicker("Example Ticker", SecurityType.STOCK, 1),
            BloombergTicker("Example Ticker", SecurityType.STOCK, 1))]
        self.assertRaises(AssertionError, alpha_model_strategy.calculate_and_place_orders)

    def test__get_current_exposure__future_ticker(self):
        """
        Test the result of _get_current_exposure function for a future ticker in case of an empty portfolio and in case
        if a position for the given specific ticker exists.
        """
        expected_current_exposure_values = []
        # Set current specific ticker to ExampleZ00 Comdty and open position in the portfolio for the current ticker
        ticker = BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1)
        self.future_ticker.get_current_specific_ticker.return_value = ticker
        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)
        # In case of empty portfolio get_signal function should have current exposure set to OUT
        futures_alpha_model_strategy.calculate_and_place_orders()
        expected_current_exposure_values.append(Exposure.OUT)
        self.alpha_model.get_signal.assert_called_with(self.future_ticker, Exposure.OUT, self.ts.timer.now(),
                                                       Frequency.DAILY)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': ticker,
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        })]
        futures_alpha_model_strategy.calculate_and_place_orders()
        self.alpha_model.get_signal.assert_called_with(self.future_ticker, Exposure.LONG, self.ts.timer.now(),
                                                       Frequency.DAILY)

        self.positions_in_portfolio = [BacktestPositionFactory.create_position(c) for c in (ticker, ticker)]
        self.assertRaises(AssertionError, futures_alpha_model_strategy.calculate_and_place_orders)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__get_current_exposure__future_ticker_rolling(self, generate_close_orders):
        """
        Test the result of _get_current_exposure function for a future ticker in case if a position for an expired
        contract exists in portfolio and the rolling should be performed.
        """
        # Set the future ticker to point to a new specific ticker, different from the one in the position from portfolio
        current_ticker = BloombergTicker("ExampleN01 Comdty", SecurityType.FUTURE, 1)
        self.future_ticker.get_current_specific_ticker.return_value = current_ticker

        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)
        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        })]
        futures_alpha_model_strategy.calculate_and_place_orders()

        self.alpha_model.get_signal.assert_called_once_with(self.future_ticker, Exposure.LONG, self.ts.timer.now(),
                                                            Frequency.DAILY)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': 10,
            'start_time': str_to_date("2000-01-01")
        }), Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        })]
        self.assertRaises(AssertionError, futures_alpha_model_strategy.calculate_and_place_orders)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__get_current_exposure__future_ticker_rolling_2(self, generate_close_orders):
        """
        Test the result of _get_current_exposure function for a future ticker in case if a position for an expired
        contract exists in portfolio and the rolling should be performed.
        """
        # Set the future ticker to point to a new specific ticker, different from the one in the position from portfolio
        current_ticker = BloombergTicker("ExampleN01 Comdty", SecurityType.FUTURE, 1)
        self.future_ticker.get_current_specific_ticker.return_value = current_ticker

        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        }), Mock(spec=BacktestPosition, **{
            'ticker.return_value': current_ticker,
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        })]
        futures_alpha_model_strategy.calculate_and_place_orders()
        self.alpha_model.get_signal.assert_called_once_with(self.future_ticker, Exposure.LONG, self.ts.timer.now(),
                                                            Frequency.DAILY)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__get_current_exposure__future_ticker_rolling_3(self, generate_close_orders):
        """
        Test the result of _get_current_exposure function for a future ticker in case if a position for an expired
        contract exists in portfolio and the rolling should be performed.
        """
        # Set the future ticker to point to a new specific ticker, different from the one in the position from portfolio
        self.future_ticker.ticker = BloombergTicker("ExampleN01 Comdty")
        futures_alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                          use_stop_losses=False)

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        }), Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleN01 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        }), Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ01 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': 20,
            'start_time': str_to_date("2000-01-02")
        })]
        self.assertRaises(AssertionError, futures_alpha_model_strategy.calculate_and_place_orders)

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
        self.future_ticker.ticker = BloombergTicker("ExampleN01 Comdty")
        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.ticker]},
                                                  use_stop_losses=False, max_open_positions=1)
        self.alpha_model.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1, Mock(),
                                                          Mock())

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.ts.position_sizer.size_signals.assert_called_with(
            [Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1, Mock(), Mock())], False, TimeInForce.OPG, Frequency.DAILY)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__adjust_number_of_open_positions_2(self, generate_close_orders):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - there is a signal with suggested exposure LONG for ExampleN01 Comdty
        - Expected output: ExampleN01 Comdty suggested exposure will be unchanged
        """
        self.future_ticker.ticker = BloombergTicker("ExampleN01 Comdty")
        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker]},
                                                  use_stop_losses=False, max_open_positions=1)
        self.alpha_model.get_signal.return_value = Signal(self.future_ticker, Exposure.LONG, 1, Mock(), Mock())

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.ts.position_sizer.size_signals.assert_called_with(
            [Signal(self.future_ticker, Exposure.LONG, 1, Mock(), Mock())], False, TimeInForce.OPG, Frequency.DAILY)

    @patch.object(FuturesRollingOrdersGenerator, 'generate_close_orders')
    def test__adjust_number_of_open_positions_3(self, generate_close_orders):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - there are 2 LONG signals for ExampleN01 Comdty and Example Ticker
        - Expected output: Example Ticker will be changed to OUT, signal for ExampleN01 Comdty will be unchanged
        """
        self.future_ticker.ticker = BloombergTicker("ExampleN01 Comdty")
        alpha_model_strategy = AlphaModelStrategy(self.ts, {self.alpha_model: [self.future_ticker, self.ticker]},
                                                  use_stop_losses=False, max_open_positions=1)
        self.alpha_model.get_signal.side_effect = lambda ticker, exposure, time, freq: Signal(ticker, Exposure.LONG, 1,
                                                                                              Mock(), Mock())

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _, _, _ = args
        expected_signals = [Signal(self.future_ticker, Exposure.LONG, 1, Mock(), Mock()),
                            Signal(self.ticker, Exposure.OUT, 1, Mock(), Mock())]
        self.assertCountEqual(signals, expected_signals)

    def test__adjust_number_of_open_positions_4(self):
        """
        Test description:
        - max number of positions is 1
        - portfolio contains position with contract ExampleZ00 Comdty
        - there is signal for ExampleZ00 Comdty with suggested exposure OUT and for Example Ticker - LONG
        - Expected output: Example Ticker will be changed to OUT
        """
        self.future_ticker.ticker = BloombergTicker("AN01 Index")

        alpha_model_strategy = AlphaModelStrategy(self.ts,
                                                  {self.alpha_model: [BloombergTicker("ExampleZ00 Comdty"),
                                                                      BloombergTicker("Example Ticker")]},
                                                  use_stop_losses=False, max_open_positions=1)

        exposures = {
            BloombergTicker("ExampleZ00 Comdty"): Exposure.OUT,
            BloombergTicker("Example Ticker"): Exposure.LONG,
        }
        self.alpha_model.get_signal.side_effect = lambda ticker, exposure, time, freq: Signal(ticker, exposures[ticker],
                                                                                              1, Mock(), Mock())

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _, _, _ = args
        expected_signals = [Signal(BloombergTicker("ExampleZ00 Comdty"), Exposure.OUT, 1, Mock(), Mock()),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1, Mock(), Mock())]
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

        self.alpha_model.get_signal.return_value = Signal(BloombergTicker("ExampleZ00 Comdty"), Exposure.LONG, 1,
                                                          Mock(), Mock())
        alpha_model_2.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1,
                                                       Mock(), Mock())

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _, _, _ = args
        expected_signals = [Signal(BloombergTicker("ExampleZ00 Comdty"), Exposure.LONG, 1, Mock(), Mock()),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1, Mock(), Mock())]
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
        self.future_ticker.ticker = BloombergTicker("ExampleN00 Comdty")
        alpha_model_2 = MagicMock()

        alpha_model_strategy = AlphaModelStrategy(self.ts, {
            self.alpha_model: [self.future_ticker],
            alpha_model_2: [BloombergTicker("Example Ticker")]
        }, use_stop_losses=False, max_open_positions=1)

        self.alpha_model.get_signal.return_value = Signal(self.future_ticker,
                                                          Exposure.LONG, 1, Mock(), Mock())
        alpha_model_2.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1, Mock(), Mock())

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _, _, _ = args
        expected_signals = [Signal(self.future_ticker, Exposure.LONG, 1, Mock(), Mock()),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1, Mock(), Mock())]
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
        self.future_ticker.ticker = BloombergTicker("ExampleN00 Comdty")
        alpha_model_2 = MagicMock()

        alpha_model_strategy = AlphaModelStrategy(self.ts, {
            self.alpha_model: [self.future_ticker],
            alpha_model_2: [BloombergTicker("Example Ticker")]
        }, use_stop_losses=False, max_open_positions=1)

        self.alpha_model.get_signal.return_value = Signal(self.future_ticker,
                                                          Exposure.OUT, 1, Mock(), Mock())
        alpha_model_2.get_signal.return_value = Signal(BloombergTicker("Example Ticker"), Exposure.LONG, 1,
                                                       Mock(), Mock())

        self.positions_in_portfolio = [Mock(spec=BacktestPosition, **{
            'ticker.return_value': BloombergTicker("ExampleZ00 Comdty", SecurityType.FUTURE, 1),
            'quantity.return_value': -10,
            'start_time': str_to_date("2000-01-01")
        })]
        alpha_model_strategy.calculate_and_place_orders()
        self.ts.position_sizer.size_signals.assert_called_once()
        args, kwargs = self.ts.position_sizer.size_signals.call_args_list[0]
        signals, _, _, _ = args
        expected_signals = [Signal(self.future_ticker, Exposure.OUT, 1, Mock(), Mock()),
                            Signal(BloombergTicker("Example Ticker"), Exposure.OUT, 1, Mock(), Mock())]
        self.assertCountEqual(signals, expected_signals)
