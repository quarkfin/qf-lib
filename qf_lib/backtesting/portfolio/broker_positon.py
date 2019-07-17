from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.portfolio.position import Position


class BrokerPosition(Position):
    def __init__(self, contract: Contract, position: float, avg_cost: float):
        self._contract = contract
        self._quantity = position
        self._avg_cost = avg_cost

    def contract(self) -> Contract:
        return self._contract

    def quantity(self) -> float:
        return self._quantity

    def avg_cost_per_share(self) -> float:
        return self._avg_cost

    def __str__(self):
        return 'BrokerPosition:\n' \
               '\tcontract: {}\n' \
               '\tquantity: {}\n' \
               '\tavg cost per share: {}\n'.format(str(self.contract()), self.quantity(), self.avg_cost_per_share())
