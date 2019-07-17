from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer


class SimplePositionSizer(PositionSizer):
    """
    This SimplePositionSizer converts signals to orders which are the size of 100% of the current portfolio value
    """

    def _generate_market_order(self, contract, signal: Signal):
        target_percentage = signal.suggested_exposure.value
        market_order_list = self._order_factory.target_percent_orders(
            {contract: target_percentage}, MarketOrder(), TimeInForce.OPG)

        if len(market_order_list) == 0:
            return None

        assert len(market_order_list) == 1, "Only one order should be generated"
        return market_order_list[0]
