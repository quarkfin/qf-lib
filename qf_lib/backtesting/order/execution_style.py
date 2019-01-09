
class ExecutionStyle(object):

    def __str__(self):
        return self.__class__.__name__


class MarketOrder(ExecutionStyle):
    def __eq__(self, other):
        return type(other) == MarketOrder


class MarketOnCloseOrder(ExecutionStyle):
    def __eq__(self, other):
        return type(other) == MarketOnCloseOrder


class StopOrder(ExecutionStyle):
    def __init__(self, stop_price: float):
        self.stop_price = stop_price

    def __str__(self):
        return "{} - stop price: {}".format(self.__class__.__name__, self.stop_price)

    def __eq__(self, other):
        if other is self:
            return True

        if not isinstance(other, StopOrder):
            return False

        return self.stop_price == other.stop_price
