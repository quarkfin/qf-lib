from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.orderfactory import OrderFactory
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number


class InitialRiskPositionSizer(PositionSizer):
    """
    This PositionSizer converts signals to orders using Initial Risk value that is predefined in the position sizer.
    Each signal will be sized based on fraction_at_risk.
    position size = Initial_Risk / signal.fraction_at_risk
    """

    def __init__(self, broker: Broker, data_handler: DataHandler, order_factory: OrderFactory,
                 contract_ticker_mapper: ContractTickerMapper, initial_risk: float):
        """
        initial_risk - should be set once for all signals. It corresponds to the value that we are willing to lose
        on single trade. For example: initial_risk = 0.02, means that we are willing to lose 2% of portfolio value in
        single trade
        """
        super().__init__(broker, data_handler, order_factory, contract_ticker_mapper)

        self._initial_risk = initial_risk

    def _generate_market_order(self, contract: Contract, signal: Signal):
        assert is_finite_number(self._initial_risk), "Initial risk has to be a finite number"
        assert is_finite_number(signal.fraction_at_risk), "fraction_at_risk has to be a finite number"

        target_percentage = self._initial_risk / signal.fraction_at_risk
        target_percentage *= signal.suggested_exposure.value  # preserve the direction (-1, 0 , 1)

        assert is_finite_number(target_percentage), "target_percentage has to be a finite number"

        market_order_list = self._order_factory.target_percent_orders({contract: target_percentage}, MarketOrder())

        if len(market_order_list) == 0:
            return None

        assert len(market_order_list) == 1, "Only one order should be generated"
        return market_order_list[0]
