from qf_lib.backtesting.qstrader.events.empty_queue_event.empty_queue_event_notifier import EmptyQueueEventNotifier
from qf_lib.backtesting.qstrader.events.end_trading_event.end_trading_event_notifier import EndTradingEventNotifier
from qf_lib.backtesting.qstrader.events.event_base import AllEventNotifier
from qf_lib.backtesting.qstrader.events.fill_event.fill_event_notifier import FillEventNotifier
from qf_lib.backtesting.qstrader.events.signal_event.signal_event_notifier import SignalEventNotifier
from qf_lib.backtesting.qstrader.events.time_event.scheduler import Scheduler
from qf_lib.common.utils.dateutils.timer import Timer


class Notifiers(object):
    """
    Convenience class grouping all notifiers together.
    """

    def __init__(self, timer: Timer):
        # when an event of certain type (e.g. BarEvent) is being dispatched by EventManager then what EventManger
        # does is it finds the notifier which corresponds to this type of event (e.g. BarEventNotifier). Then
        # the notifier notifies all its listeners about an event which occurred. However there might be some listeners
        # which are listening to the more general type of event (e.g. PriceEvent) and they should also be notified.
        # That's why the notifier will also call a notifier specific to more general type of events
        # (e.g. PriceEventNotifier) which will then notify all its listeners. The chain of calls on different
        # notification managers goes on until the AllEventNotifier is called. That one corresponds to the most general
        # type of events which is the Event. When listeners subscribed to the Event are notified in the end
        # the process of notifications is over.
        #
        # Because of the fact that each notifier also calls the notifier for events of more general type
        # the notifier must have a reference to this "more general" notifier. Most of events inherit directly from
        # the Event type. That's why most of notifiers will need a reference to AllEventNotifier.
        self.all_event_notifier = AllEventNotifier()
        self.empty_queue_event_notifier = EmptyQueueEventNotifier(self.all_event_notifier)
        self.end_trading_event_notifier = EndTradingEventNotifier(self.all_event_notifier)
        self.fill_event_notifier = FillEventNotifier(self.all_event_notifier)
        self.signal_event_notifier = SignalEventNotifier(self.all_event_notifier)
        self.scheduler = Scheduler(timer)
