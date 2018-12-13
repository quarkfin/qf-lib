from qf_lib.backtesting.order.execution_style import MarketOrder, StopOrder
from qf_lib.backtesting.order.order import Order
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer


class SimplePositionSizer(PositionSizer):
    """
    This SimplePositionSizer converts signals to orders which are the size of 100% of the current portfolio value
    """

    def _generate_market_order(self, contract, signal):
        target_percentage = signal.suggested_exposure.value
        market_order_list = self._order_factory.target_percent_orders({contract: target_percentage}, MarketOrder())

        if len(market_order_list) == 0:
            return None

        assert len(market_order_list) == 1, "Only one order should be generated"
        return market_order_list[0]

    def _generate_stop_order(self, contract, signal, market_order: Order):
        stop_price = self._calculate_stop_price(signal)

        # stop_quantity = existing position size + recent market orders quantity
        stop_quantity = self._get_existing_position_quantity(contract)

        if market_order is not None:
            stop_quantity += market_order.quantity

        # put minus before the quantity as stop order has to go in the opposite direction
        stop_orders = self._order_factory.orders({contract: -stop_quantity}, StopOrder(stop_price))

        assert len(stop_orders) == 1, "Only one order should be generated"
        return stop_orders[0]
