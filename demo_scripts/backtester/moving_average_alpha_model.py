import talib

from qf_lib.backtesting.alpha_model.alpha_model import AlphaModel, AlphaModelSettings
from qf_lib.backtesting.alpha_model.exposure_enum import Exposure
from qf_lib.backtesting.data_handler.data_handler import DataHandler
from qf_lib.common.enums.price_field import PriceField
from qf_lib.common.tickers.tickers import Ticker


class MovingAverageAlphaModel(AlphaModel):
    """
    This is an example of a simple AlphaModel. It applies two Exponential Moving Averages of different time periods
    on the recent market close prices of an asset to determine the suggested move. It suggests to go LONG on this asset
    if the shorter close prices moving average exceeds the longer one. Otherwise it suggests to go SHORT.
    """

    settings = AlphaModelSettings(
        parameters=(5, 20),
        risk_estimation_factor=1.25
    )

    def __init__(self, fast_time_period: int, slow_time_period: int,
                 risk_estimation_factor: float, data_handler: DataHandler):
        super().__init__(risk_estimation_factor, data_handler)

        self.fast_time_period = fast_time_period
        self.slow_time_period = slow_time_period

        if fast_time_period < 3:
            raise ValueError('timeperiods shorter than 3 are pointless')
        if slow_time_period <= fast_time_period:
            raise ValueError('slow MA time period should be longer than fast MA time period')

    def calculate_exposure(self, ticker: Ticker, current_exposure: Exposure) -> Exposure:
        num_of_bars_needed = self.slow_time_period
        close_tms = self.data_handler.historical_price(ticker, PriceField.Close, num_of_bars_needed)

        fast_ma = talib.MA(close_tms, self.fast_time_period, matype=1)  # MA type: Exponential MA
        slow_ma = talib.MA(close_tms, self.slow_time_period, matype=1)  # MA type: Exponential MA

        if fast_ma[-1] > slow_ma[-1]:
            return Exposure.LONG
        else:
            return Exposure.SHORT
