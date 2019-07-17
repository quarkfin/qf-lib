from qf_lib.backtesting.alpha_model.signal import Signal
from qf_lib.backtesting.broker.broker import Broker
from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.contract.contract_to_ticker_conversion.base import ContractTickerMapper
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.backtesting.order.execution_style import MarketOrder
from qf_lib.backtesting.order.order_factory import OrderFactory
from qf_lib.backtesting.order.time_in_force import TimeInForce
from qf_lib.backtesting.position_sizer.position_sizer import PositionSizer
from qf_lib.common.utils.numberutils.is_finite_number import is_finite_number


class InitialRiskPositionSizer(PositionSizer):
    """
    This PositionSizer converts signals to orders using Initial Risk value that is predefined in the position sizer.
    Each signal will be sized based on fraction_at_risk.
    position size = Initial_Risk / signal.fraction_at_risk
    """

    def __init__(self, broker: Broker, data_handler: DataHandler, order_factory: OrderFactory,
                 contract_ticker_mapper: ContractTickerMapper, initial_risk: float, max_target_percentage=1.5):
        """
        initial_risk
            should be set once for all signals. It corresponds to the value that we are willing to lose
            on single trade. For example: initial_risk = 0.02, means that we are willing to lose 2% of portfolio value in
            single trade
        max_target_percentage
            max leverage that is accepted by the position sizer.
        """
        super().__init__(broker, data_handler, order_factory, contract_ticker_mapper)

        self._initial_risk = initial_risk
        self.max_target_percentage = max_target_percentage
        self.logger.info("Initial Risk: {}".format(initial_risk))

    def _generate_market_order(self, contract: Contract, signal: Signal):
        assert is_finite_number(self._initial_risk), "Initial risk has to be a finite number"
        assert is_finite_number(signal.fraction_at_risk), "fraction_at_risk has to be a finite number"

        target_percentage = self._initial_risk / signal.fraction_at_risk
        self.logger.info("Target Percentage: {}".format(target_percentage))

        target_percentage = self._cap_max_target_percentage(target_percentage)

        target_percentage *= signal.suggested_exposure.value  # preserve the direction (-1, 0 , 1)
        self.logger.info("Target Percentage considering direction: {}".format(target_percentage))

        assert is_finite_number(target_percentage), "target_percentage has to be a finite number"

        market_order_list = self._order_factory.target_percent_orders(
            {contract: target_percentage}, MarketOrder(), TimeInForce.OPG)
        if len(market_order_list) == 0:
            return None

        assert len(market_order_list) == 1, "Only one order should be generated"
        return market_order_list[0]

    def _cap_max_target_percentage(self, initial_target_percentage: float):
        """
        Sometimes the target percentage can be excessive to be executed by the broker (might exceed margin requirement)
        Cap the target percentage to the max value defined in this function
        """
        if initial_target_percentage > self.max_target_percentage:
            self.logger.info("Target Percentage: {} above the maximum of {}. Setting the target percentage to {}"
                             .format(initial_target_percentage, self.max_target_percentage, self.max_target_percentage))
            return self.max_target_percentage
        return initial_target_percentage
