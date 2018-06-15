import unittest

from qf_lib.backtesting.contract.contract import Contract
from qf_lib.backtesting.order_fill import OrderFill
from qf_lib.backtesting.portfolio.backtest_position import BacktestPosition
from qf_lib.common.utils.dateutils.string_to_date import str_to_date


class TestPosition(unittest.TestCase):
    """
    Tests for the BacktestPosition class. For tests on PnL please see this website:
    https://www.tradingtechnologies.com/help/fix-adapter-reference/pl-calculation-algorithm/understanding-pl-calculations/
    """

    def setUp(self):
        self.contract = Contract('AAPL US Equity', security_type='STK', exchange='NYSE')
        self.time = str_to_date('2017-01-01')  # dummy time

    def test_creating_empty_position(self):
        position = BacktestPosition(self.contract)
        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.number_of_shares, 0)
        self.assertEqual(position.current_price, 0)
        self.assertEqual(position.market_value, 0.0)
        self.assertEqual(position.cost_basis(), 0.0)
        self.assertEqual(position.avg_cost_per_share(), 0.0)
        self.assertEqual(position.unrealised_pnl(), 0.0)
        self.assertEqual(position.realized_pnl(), 0.0)

    def test_initial_fill_position(self):
        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, 50, 100, 5))
        position.update_price(110, 120)

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.number_of_shares, 50)
        self.assertEqual(position.current_price, 110)
        self.assertEqual(position.market_value, 50*110)
        self.assertEqual(position.cost_basis(), 50*100+5)
        self.assertEqual(position.avg_cost_per_share(), (50 * 100 + 5) / 50)
        self.assertEqual(position.unrealised_pnl(), 50*110 - (50*100+5))

    def test_without_commission_position(self):
        position = BacktestPosition(self.contract)

        position.transact_order_fill(OrderFill(self.time, self.contract, 50, 100, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, 30, 120, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 175, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, -30, 160, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, 10, 150, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, 10, 170, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 150, 0))
        position.update_price(110, 120)

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.number_of_shares, 30)
        self.assertEqual(position.current_price, 110)
        self.assertEqual(position.market_value, 30*110)
        self.assertAlmostEqual(position.cost_basis(),  16.6666666667*30, places=6)
        self.assertEqual(position.avg_cost_per_share(), 118.0)
        self.assertAlmostEqual(position.unrealised_pnl(), 30*110 - 16.6666666667*30, places=6)

    def test_position(self):
        position = BacktestPosition(self.contract)

        position.transact_order_fill(OrderFill(self.time, self.contract, 50, 100, 5))
        position.transact_order_fill(OrderFill(self.time, self.contract, 30, 120, 3))
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 175, 2))
        position.transact_order_fill(OrderFill(self.time, self.contract, -30, 160, 1))
        position.transact_order_fill(OrderFill(self.time, self.contract, 10, 150, 7))
        position.transact_order_fill(OrderFill(self.time, self.contract, 10, 170, 4))
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 150, 5))
        position.update_price(110, 120)

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.number_of_shares, 30)
        self.assertEqual(position.current_price, 110)
        self.assertEqual(position.market_value, 30*110)
        self.assertAlmostEqual(position.cost_basis(),  17.5666666666*30, places=6)
        self.assertEqual(position.avg_cost_per_share(), 118.19)
        self.assertAlmostEqual(position.unrealised_pnl(), 30*110 - 17.5666666666*30, places=6)

    def test_position_close(self):
        position = BacktestPosition(self.contract)
        self.assertEqual(position.is_closed, False)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        self.assertEqual(position.is_closed, False)
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 120, 20))
        self.assertEqual(position.is_closed, False)
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 110, 20))
        self.assertEqual(position.is_closed, True)

    def test_position_stats_on_close(self):
        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        position.update_price(110, 120)
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 120, 0))

        self.assertEqual(position.contract(), self.contract)
        self.assertEqual(position.number_of_shares, 0)
        self.assertEqual(position.current_price, 110)
        self.assertEqual(position.market_value, 0)
        self.assertAlmostEqual(position.cost_basis(), 0, places=6)
        self.assertEqual(position.avg_cost_per_share(), 100)
        self.assertAlmostEqual(position.unrealised_pnl(), 0, places=6)
        self.assertEqual(position.realized_pnl(), 20*20)

    def test_position_direction(self):
        position = BacktestPosition(self.contract)
        self.assertEqual(position.direction, 0)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        self.assertEqual(position.direction, 1)
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 100, 0))
        self.assertEqual(position.direction, 1)
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 100, 0))
        self.assertEqual(position.direction, 1)

        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 100, 0))
        self.assertEqual(position.direction, -1)

        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        with self.assertRaises(AssertionError):
            position.transact_order_fill(OrderFill(self.time, self.contract, -21, 100, 0))

    def test_closed_position(self):
        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 100, 0))

        with self.assertRaises(AssertionError):
            position.transact_order_fill(OrderFill(self.time, self.contract, 1, 100, 0))

        with self.assertRaises(AssertionError):
            position.transact_order_fill(OrderFill(self.time, self.contract, -1, 100, 0))

        with self.assertRaises(AssertionError):
            position.update_price(110, 120)

    def test_realised_pnl(self):
        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 120, 20))
        self.assertEqual(position.realized_pnl(), 180)

        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 80, 20))
        self.assertEqual(position.realized_pnl(), -220)

        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 100, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, 10, 120, 20))
        self.assertEqual(position.realized_pnl(), -220)

        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, -20, 100, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, 10, 80, 20))
        self.assertEqual(position.realized_pnl(), 180)

        position = BacktestPosition(self.contract)
        position.transact_order_fill(OrderFill(self.time, self.contract, 20, 100, 0))
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 120, 20))
        self.assertEqual(position.realized_pnl(), 180)
        position.transact_order_fill(OrderFill(self.time, self.contract, -10, 110, 20))
        self.assertEqual(position.realized_pnl(), 260)


if __name__ == "__main__":
    unittest.main()
