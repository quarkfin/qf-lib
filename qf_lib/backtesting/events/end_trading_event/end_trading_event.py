from datetime import datetime
from typing import Optional

from qf_lib.backtesting.events.event_base import Event


class EndTradingEvent(Event):
    """
    Occurs when the trading should stop (e.g. when the backtest should be terminated).
    """

    def __init__(self, time: Optional[datetime]) -> None:
        super().__init__(time)
