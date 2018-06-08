import unittest
from typing import List
from unittest import TestCase

from qf_lib.backtesting.qstrader.contract.contract import Contract
from qf_lib.backtesting.qstrader.events.empty_queue_event.empty_queue_event import EmptyQueueEvent
from qf_lib.backtesting.qstrader.events.empty_queue_event.empty_queue_event_listener import EmptyQueueEventListener
from qf_lib.backtesting.qstrader.events.end_trading_event.end_trading_event import EndTradingEvent
from qf_lib.backtesting.qstrader.events.end_trading_event.end_trading_event_listener import EndTradingEventListener
from qf_lib.backtesting.qstrader.events.event_base import AllEventListener, Event
from qf_lib.backtesting.qstrader.events.event_manager import EventManager
from qf_lib.backtesting.qstrader.events.fill_event.fill_event import FillEvent
from qf_lib.backtesting.qstrader.events.fill_event.fill_event_listener import FillEventListener
from qf_lib.backtesting.qstrader.events.signal_event.signal_event import SignalEvent
from qf_lib.backtesting.qstrader.events.signal_event.signal_event_listener import SignalEventListener
from qf_lib.backtesting.qstrader.events.time_event.after_market_close_event import AfterMarketCloseEvent
from qf_lib.backtesting.qstrader.events.time_event.before_market_open_event import BeforeMarketOpenEvent
from qf_lib.backtesting.qstrader.events.time_event.market_close_event import MarketCloseEvent
from qf_lib.backtesting.qstrader.events.time_event.market_open_event import MarketOpenEvent
from qf_lib.backtesting.qstrader.events.time_flow_controller import BacktestTimeFlowController
from qf_lib.backtesting.qstrader.trading_session.notifiers import Notifiers
from qf_lib.common.utils.dateutils.date_format import DateFormat
from qf_lib.common.utils.dateutils.string_to_date import str_to_date
from qf_lib.common.utils.dateutils.timer import SettableTimer, Timer
from qf_lib.testing_tools.containers_comparison import assert_lists_equal


class DummyListener(AllEventListener, EmptyQueueEventListener, EndTradingEventListener, FillEventListener,
                    SignalEventListener):
    """
    A "driver" class used for the integration test. It simulates the behavior of a Strategy, PortfolioHandler,
    ExecutionHandler and it also ends the simulation (when the BeforeMarketOpenEvent occurs for the second time).
    """

    def __init__(self, notifiers: Notifiers, event_manager: EventManager, timer: Timer):
        self.registered_events = []  # type: List[Event]

        self.event_manager = event_manager
        self.timer = timer

        notifiers.empty_queue_event_notifier.subscribe(self)
        notifiers.end_trading_event_notifier.subscribe(self)
        notifiers.fill_event_notifier.subscribe(self)
        notifiers.signal_event_notifier.subscribe(self)

        notifiers.scheduler.subscribe(MarketOpenEvent, self)
        notifiers.scheduler.subscribe(BeforeMarketOpenEvent, self)
        notifiers.scheduler.subscribe(AfterMarketCloseEvent, self)
        notifiers.scheduler.subscribe(MarketCloseEvent, self)

    def on_empty_queue_event(self, event: EmptyQueueEvent):
        self._register_event(event)

    def on_end_trading_event(self, event: EndTradingEvent):
        self._register_event(event)

    def on_fill_event(self, event: FillEvent):
        self._register_event(event)

    def on_signal_event(self, event: SignalEvent):
        self._register_event(event)

    def on_before_market_open(self, event: BeforeMarketOpenEvent):
        self._register_event(event)

        self.event_manager.publish(
            SignalEvent(time=self.timer.now(), suggested_orders=[])
        )

    def on_market_open(self, event: MarketOpenEvent):
        self._register_event(event)
        test_contract = Contract(symbol="TEST_SYMBOL", security_type="STK", exchange="NASDAQ")
        self.event_manager.publish(
            FillEvent(self.timer.now(), contract=test_contract, quantity=8, price=112.09, commission=0.001)
        )

    def on_after_market_close(self, event: AfterMarketCloseEvent):
        self._register_event(event)

    def on_market_close(self, event: MarketCloseEvent):
        self._register_event(event)

    def _register_event(self, event: Event) -> None:
        self.registered_events.append(event)


class TestEventManagement(TestCase):
    """
    Tests the interaction among: EventManager, notifiers (including Scheduler) and the BacktestTimeFlowController.
    Tests:
    - if events are published correctly,
    - if corresponding listeners are notified of events in the right order,
    - if BacktestTimeFlowController creates TimeEvents at proper time.
    """

    def test_event_management(self):
        timer = SettableTimer(initial_time=str_to_date("2018-04-10 00:00:00.000000", DateFormat.FULL_ISO))
        end_date = str_to_date("2018-04-11")

        notifiers = Notifiers(timer)

        event_manager = self._create_event_manager(timer, notifiers)
        BacktestTimeFlowController(
            notifiers.scheduler, event_manager, timer, notifiers.empty_queue_event_notifier, end_date
        )

        listener = DummyListener(notifiers, event_manager, timer)

        last_event = None
        while type(last_event) != EndTradingEvent:
            event_manager.dispatch_next_event()
            last_event = listener.registered_events[-1]

        expected_events = [
            (EmptyQueueEvent, str_to_date("2018-04-10 00:00:00.000000", DateFormat.FULL_ISO)),
            (BeforeMarketOpenEvent, str_to_date("2018-04-10 08:00:00.000000", DateFormat.FULL_ISO)),
            (SignalEvent, str_to_date("2018-04-10 08:00:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 08:00:00.000000", DateFormat.FULL_ISO)),
            (MarketOpenEvent, str_to_date("2018-04-10 09:30:00.000000", DateFormat.FULL_ISO)),
            (FillEvent, str_to_date("2018-04-10 09:30:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 09:30:00.000000", DateFormat.FULL_ISO)),
            (MarketCloseEvent, str_to_date("2018-04-10 16:00:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 16:00:00.000000", DateFormat.FULL_ISO)),
            (AfterMarketCloseEvent, str_to_date("2018-04-10 18:00:00.000000", DateFormat.FULL_ISO)),
            (EmptyQueueEvent, str_to_date("2018-04-10 18:00:00.000000", DateFormat.FULL_ISO)),
            (EndTradingEvent, str_to_date("2018-04-11 00:00:00.000000", DateFormat.FULL_ISO)),
        ]

        actual_events = [(type(event), event.time) for event in listener.registered_events]

        assert_lists_equal(expected_events, actual_events, absolute_tolerance=0.0)

    def _create_event_manager(self, timer, notifiers):
        event_manager = EventManager(timer)

        event_manager.register_notifiers([
            notifiers.empty_queue_event_notifier,
            notifiers.end_trading_event_notifier,
            notifiers.fill_event_notifier,
            notifiers.signal_event_notifier,
            notifiers.scheduler
        ])
        return event_manager


if __name__ == '__main__':
    unittest.main()
