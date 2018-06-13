from datetime import datetime

from qf_lib.backtesting.events.time_event.regular_date_time_rule import RegularDateTimeRule
from qf_lib.backtesting.events.time_event.regular_time_event import RegularTimeEvent
from qf_lib.common.utils.dateutils.relative_delta import RelativeDelta


class MarketCloseEvent(RegularTimeEvent):
    """
    Rule which is triggered every day when the market opens (16:00 for NASDAQ and NYSE).

    The listeners for this event should implement the on_market_close() method.
    """

    _trigger_time = {"hour": 16, "minute": 0, "second": 0, "microsecond": 0}
    _trigger_time_rule = RegularDateTimeRule(**_trigger_time)

    @classmethod
    def trigger_time(cls) -> RelativeDelta:
        return RelativeDelta(**cls._trigger_time)

    @classmethod
    def next_trigger_time(cls, now: datetime) -> datetime:
        next_trigger_time = cls._trigger_time_rule.next_trigger_time(now)
        return next_trigger_time

    def notify(self, listener) -> None:
        listener.on_market_close(self)
